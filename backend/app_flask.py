"""
DocuVaultAI — Flask REST API Backend (Unit 3: Web Frameworks)
Provides RESTful HTTP microservices for document ingestion, binary verification,
storage mode toggling, working-day action planning, RAG AI chat, and audit trails.
"""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from backend.api_client import LLMClient, PublicHolidayClient
from auth.keycloak_client import KeycloakClient
from auth.local_auth import LocalAuthManager
from auth.tier_manager import TierConfig, TierManager, UserTier
from core.base_document import BaseDocument, DocumentFactory
from core.catalog_manager import CatalogManager
from core.exceptions import (
    AuthenticationError,
    CorruptFileError,
    DocuVaultError,
    FeatureLockedError,
    TamperedFileError,
    TierLimitExceededError,
)
from core.organizer import FileOrganizerDaemon
from core.parsers.binary_parser import BinaryParser
from core.pii_redactor import PIIRedactor
from core.storage_providers import CloudStorageProvider, LocalStorageProvider
from core.vector_search import VectorSearchEngine
from core.folder_tracker import DirectoryTracker
from core.document_analyzer import DocumentAnalyzer
from core.batch_exporter import BatchDossierExporter
from core.retention_policy import RetentionPolicyManager
from core.ai_assistant import ExplainableAIAssistant

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for Streamlit and desktop bridge

# App state and services
active_storage_mode = "Local Drive"  # or "Cloud Vault"
local_storage = LocalStorageProvider(root_dir="vault/local")
cloud_storage = CloudStorageProvider(mirror_dir="vault/cloud_mirror")
catalog_mgr = CatalogManager()
vector_engine = VectorSearchEngine()
holiday_client = PublicHolidayClient(default_country="US")
llm_client = LLMClient()
organizer = FileOrganizerDaemon(vault_root="vault")
local_auth = LocalAuthManager()
keycloak_client = KeycloakClient()
tracker = DirectoryTracker()
assistant = ExplainableAIAssistant(vector_engine)

# In-memory document registry for quick lookup: doc_id -> BaseDocument
document_store: Dict[str, BaseDocument] = {}


def get_current_storage():
    """Returns the currently active storage provider instance."""
    return local_storage if active_storage_mode == "Local Drive" else cloud_storage


# -------------------------------------------------------------------------
# Custom Error Handlers
# -------------------------------------------------------------------------

@app.errorhandler(DocuVaultError)
def handle_docuvault_error(err: DocuVaultError):
    """Formats custom domain exceptions as clean JSON responses."""
    return jsonify({
        "status": "error",
        "error_code": err.error_code,
        "message": err.message,
        "context": err.context,
        "timestamp": err.timestamp,
    }), 400


@app.errorhandler(TierLimitExceededError)
def handle_tier_limit(err: TierLimitExceededError):
    return jsonify({
        "status": "error",
        "error_code": err.error_code,
        "message": err.message,
        "resource": err.resource_name,
        "current_count": err.current_count,
        "limit": err.limit,
        "tier": err.tier,
        "suggestion": err.suggestion,
    }), 403


@app.errorhandler(FeatureLockedError)
def handle_feature_locked(err: FeatureLockedError):
    return jsonify({
        "status": "error",
        "error_code": err.error_code,
        "message": err.message,
        "feature": err.feature_name,
        "tier": err.tier,
        "suggestion": err.suggestion,
    }), 403


@app.errorhandler(AuthenticationError)
def handle_auth_error(err: AuthenticationError):
    return jsonify({
        "status": "error",
        "error_code": err.error_code,
        "message": err.message,
        "username_or_email": err.username_or_email,
    }), 401


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"status": "error", "error_code": "ERR_NOT_FOUND", "message": "Resource not found"}), 404


@app.errorhandler(500)
def handle_500(err):
    return jsonify({"status": "error", "error_code": "ERR_INTERNAL", "message": str(err)}), 500


# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health status and general system metrics."""
    return jsonify({
        "status": "healthy",
        "service": "DocuVaultAI REST Engine",
        "active_storage_mode": active_storage_mode,
        "cloud_online": cloud_storage.is_online,
        "indexed_documents": len(document_store),
        "indexed_chunks": len(vector_engine.chunks),
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/storage/mode", methods=["GET", "POST"])
def storage_mode():
    """Get or toggle active storage mode between [Local Drive] and [Cloud Vault]."""
    global active_storage_mode
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        new_mode = data.get("mode")
        tier_str = request.headers.get("X-User-Tier") or data.get("tier")
        if new_mode in ["Local Drive", "Cloud Vault"]:
            if new_mode == "Cloud Vault" and tier_str and not TierManager.can_access_feature(tier_str, "cloud_sync"):
                raise FeatureLockedError("cloud_sync", tier_str, "Cloud Vault mirror requires Pro Plan.")
            active_storage_mode = new_mode
            if new_mode == "Cloud Vault":
                cloud_storage.check_connection()
            return jsonify({
                "status": "success",
                "active_storage_mode": active_storage_mode,
                "message": f"Storage mode switched to {active_storage_mode}",
            })
        return jsonify({"status": "error", "message": "Invalid mode. Use 'Local Drive' or 'Cloud Vault'"}), 400

    return jsonify({
        "active_storage_mode": active_storage_mode,
        "cloud_connected": cloud_storage.check_connection(),
    })


@app.route("/api/storage/metrics", methods=["GET"])
def storage_metrics():
    """Returns storage metrics and distribution between Local and Cloud."""
    dist = catalog_mgr.get_storage_distribution()
    cats = catalog_mgr.get_category_metrics()
    return jsonify({
        "storage_distribution": dist,
        "category_metrics": cats,
        "active_storage_mode": active_storage_mode,
    })


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List indexed documents with optional category or storage mode filters."""
    category = request.args.get("category")
    storage = request.args.get("storage_mode")

    records = catalog_mgr.to_records_list()

    if category and category != "All":
        records = [r for r in records if r.get("category") == category]
    if storage and storage != "All":
        records = [r for r in records if r.get("storage_mode") == storage]

    return jsonify({
        "total": len(records),
        "documents": records,
    })


@app.route("/api/documents/upload", methods=["POST"])
def upload_document():
    """
    Ingest a new document:
    1. Validates magic bytes via BinaryParser.
    2. Computes SHA-256 hash.
    3. Ingests polymorphic document class via DocumentFactory.
    4. Indexes text chunks into pure NumPy VectorSearchEngine.
    5. Saves into active storage provider and registers in MultiIndex CatalogManager.
    """
    tier_str = request.headers.get("X-User-Tier") or request.form.get("tier") or (request.get_json(silent=True) or {}).get("tier")
    if tier_str:
        TierManager.check_document_limit(tier_str, len(document_store))

    if "file" not in request.files:
        # Check if json text upload
        payload = request.get_json(silent=True)
        if not payload or "text" not in payload:
            return jsonify({"status": "error", "message": "No file or text payload uploaded"}), 400

        filename = payload.get("filename", f"doc_{int(datetime.now().timestamp())}.txt")
        raw_text = payload["text"]
        cat_hint = payload.get("category")

        # Save to storage
        storage = get_current_storage()
        rel_path = f"{cat_hint or 'General'}/{filename}"
        storage.save_file(rel_path, raw_text.encode("utf-8"))

        doc = DocumentFactory.create_document(
            filepath=str(storage.base_dir / rel_path),
            raw_text=raw_text,
            category_hint=cat_hint,
            enforce_magic_bytes=False,
        )
    else:
        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({"status": "error", "message": "Uploaded file has no filename"}), 400

        filename = uploaded_file.filename
        cat_hint = request.form.get("category")
        content_bytes = uploaded_file.read()

        storage = get_current_storage()
        rel_path = f"{cat_hint or 'General'}/{filename}"
        saved_path = storage.save_file(rel_path, content_bytes)

        # Ingest and validate
        doc = DocumentFactory.create_document(
            filepath=saved_path,
            category_hint=cat_hint,
            enforce_magic_bytes=True,
        )

    # Register document
    document_store[doc.doc_id] = doc
    catalog_mgr.add_document(doc.to_dict(), storage_mode=active_storage_mode)

    # Vector indexing for RAG
    vector_engine.add_document_chunks(
        doc_id=doc.doc_id,
        filename=doc.filename,
        category=doc.get_category(),
        pages=doc.pages,
    )
    vector_engine.build_index()

    # Log in audit
    organizer.logger.log_operation(
        level="INFO",
        action="INGEST",
        filename=doc.filename,
        category=doc.get_category(),
        size_bytes=doc.size_bytes,
        destination=f"{active_storage_mode}/{rel_path}",
        extra=f"ID: {doc.doc_id} | Hash: {doc.sha256_hash[:10]}...",
    )

    return jsonify({
        "status": "success",
        "message": f"Document '{doc.filename}' successfully indexed and cataloged.",
        "document": doc.to_dict(),
    }), 201


@app.route("/api/documents/<doc_id>", methods=["GET"])
def get_document_details(doc_id: str):
    """Retrieve full document metadata, extracted clauses, entities, and raw text."""
    doc = document_store.get(doc_id)
    if not doc:
        return jsonify({"status": "error", "message": f"Document ID '{doc_id}' not found."}), 404

    data = doc.to_dict()
    data["raw_text_sample"] = doc.raw_text[:2000]
    data["deadlines"] = doc.extract_deadlines()
    return jsonify(data)


@app.route("/api/documents/<doc_id>/verify", methods=["POST"])
def verify_document_integrity(doc_id: str):
    """Performs live cryptographic integrity verification against the recorded SHA-256."""
    doc = document_store.get(doc_id)
    if not doc:
        return jsonify({"status": "error", "message": f"Document ID '{doc_id}' not found."}), 404

    is_valid = doc.verify_integrity()
    return jsonify({
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "status": doc.status,
        "verified": is_valid,
        "current_hash": doc.sha256_hash,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/chat", methods=["POST"])
def chat_rag():
    """
    RAG Semantic Retrieval & AI Completion:
    1. Pure NumPy TF-IDF cosine similarity search.
    2. Boolean masking filter by category.
    3. Multi-LLM completion with exact citations: Source: [Filename], Page: [Page Number].
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    category_filter = data.get("category", "All")
    top_k = int(data.get("top_k", 4))
    tier_str = request.headers.get("X-User-Tier") or data.get("tier")
    if tier_str:
        session_query_count = int(data.get("session_query_count", 0))
        TierManager.check_chat_limit(tier_str, session_query_count)

    # Execute vector retrieval
    results = vector_engine.search(
        query=query,
        top_k=top_k,
        category_filter=category_filter,
    )

    # Generate cited LLM answer
    rag_response = llm_client.generate_rag_response(query, results)

    # Generate Matplotlib similarity distribution plot
    plot_file = None
    if results:
        plot_path = f"vault/plots/sim_{int(datetime.now().timestamp())}.png"
        plot_file = vector_engine.generate_similarity_plot(query, results, output_image_path=plot_path)

    return jsonify({
        "query": query,
        "answer": rag_response["answer"],
        "provider": rag_response["provider"],
        "citations": rag_response["citations"],
        "retrieved_chunks": results,
        "plot_path": plot_file,
    })


@app.route("/api/deadlines", methods=["GET"])
def get_deadlines_plan():
    """
    Action Planner & Working-Day Expiry Engine:
    Extracts upcoming deadlines and adjusts them according to the Nager.Date holiday API.
    """
    country_code = request.args.get("country", "US")
    today = date.today()

    all_deadlines = []
    for doc_id, doc in document_store.items():
        extracted = doc.extract_deadlines()
        extracted_dates = doc.extract_dates()

        for d_str in extracted_dates:
            # Attempt to parse ISO or standard date
            try:
                # Clean string
                clean_d = d_str.replace("/", "-")
                parts = clean_d.split("-")
                if len(parts) == 3 and len(parts[0]) == 4:
                    target_d = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    calc = holiday_client.calculate_working_deadline(
                        start_date=target_d,
                        business_days=0,
                        country_code=country_code,
                    )
                    all_deadlines.append({
                        "doc_id": doc.doc_id,
                        "filename": doc.filename,
                        "category": doc.get_category(),
                        "original_deadline": calc["original_date"],
                        "adjusted_working_deadline": calc["working_deadline"],
                        "was_shifted": calc["was_shifted"],
                        "shift_reason": calc["shift_reason"],
                        "status": "Upcoming" if target_d >= today else "Expired",
                    })
            except Exception:
                pass

    return jsonify({
        "country_code": country_code,
        "total_deadlines": len(all_deadlines),
        "deadlines": all_deadlines,
    })


@app.route("/api/audit-log", methods=["GET"])
def get_audit_log():
    """Fetch the latest operations audit log from file_ops.log."""
    logs = organizer.logger.get_recent_logs(max_lines=100)
    return jsonify({
        "total_lines": len(logs),
        "log_entries": logs,
    })


@app.route("/api/documents/sort", methods=["POST"])
def trigger_sorter():
    """Triggers the automated file organizer daemon on pending files in vault/intake."""
    results = organizer.process_intake_folder()
    return jsonify({
        "status": "success",
        "processed_count": len(results),
        "results": results,
    })


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    country = data.get("country", "Global").strip()
    tier = data.get("tier", UserTier.FREE.value)

    if not email or not password or not full_name:
        return jsonify({"status": "error", "message": "Email, password, and full name are required."}), 400

    user_info = local_auth.register_user(email=email, password=password, full_name=full_name, country=country, tier=tier)
    return jsonify({
        "status": "success",
        "message": "User registered successfully.",
        "user": user_info,
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required."}), 400

    user_info = keycloak_client.authenticate_password(email, password)
    return jsonify({
        "status": "success",
        "message": "Authenticated successfully.",
        "user": user_info,
    })


@app.route("/api/auth/upgrade", methods=["POST"])
def auth_upgrade():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    new_tier = data.get("tier", UserTier.PRO.value)

    if not email:
        return jsonify({"status": "error", "message": "Email is required."}), 400

    success = local_auth.update_user_tier(email, new_tier)
    user_info = local_auth.get_user(email)
    if not user_info:
        return jsonify({"status": "error", "message": "User not found."}), 404

    return jsonify({
        "status": "success",
        "message": f"User upgraded to {new_tier}.",
        "user": user_info,
    })


@app.route("/api/auth/profile", methods=["GET"])
def auth_profile():
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"status": "error", "message": "Email query parameter required."}), 400
    user = local_auth.get_user(email)
    if not user:
        return jsonify({"status": "error", "message": "User not found."}), 404
    tier = UserTier.from_str(user.get("tier", "Free"))
    cfg = TierConfig.get(tier)
    return jsonify({
        "user": user,
        "limits": cfg,
    })


@app.route("/api/documents/<doc_id>/redact", methods=["POST"])
def redact_document_endpoint(doc_id: str):
    tier_str = request.headers.get("X-User-Tier") or (request.get_json(silent=True) or {}).get("tier", "Free")
    if not TierManager.can_access_feature(tier_str, "pii_redaction"):
        raise FeatureLockedError("pii_redaction", tier_str, "Automated PII redaction requires Pro Plan.")

    doc = document_store.get(doc_id)
    if not doc:
        return jsonify({"status": "error", "message": f"Document ID '{doc_id}' not found."}), 404

    sanitized, detections = PIIRedactor.redact_text(doc.raw_text)
    return jsonify({
        "doc_id": doc_id,
        "filename": doc.filename,
        "total_redactions": len(detections),
        "detections": detections,
        "sanitized_preview": sanitized[:2000],
    })


# -------------------------------------------------------------------------
# Git-Like Directory Tracker Endpoints
# -------------------------------------------------------------------------

@app.route("/api/tracker/folders", methods=["GET", "POST", "DELETE"])
def tracker_folders_endpoint():
    """Manage monitored directories for automated Git-like ingestion."""
    if request.method == "GET":
        folders = tracker.get_watched_folders()
        return jsonify({
            "status": "success",
            "watched_folders": folders,
            "total_monitored": len(folders),
        })

    data = request.get_json(silent=True) or {}
    folder_path = data.get("folder_path", "").strip()
    if not folder_path:
        return jsonify({"status": "error", "message": "folder_path is required."}), 400

    if request.method == "POST":
        success = tracker.add_watched_folder(folder_path)
        if success:
            discovered = tracker.scan_folder(folder_path)
            for d in discovered:
                doc_id = d.get("doc_id")
                if doc_id:
                    catalog_mgr.add_document(d)
            return jsonify({
                "status": "success",
                "message": f"Folder added to tracking.",
                "folder_path": folder_path,
                "ingested_count": len(discovered),
            })
        return jsonify({"status": "error", "message": "Invalid directory or already watched."}), 400

    elif request.method == "DELETE":
        removed = tracker.remove_watched_folder(folder_path)
        return jsonify({
            "status": "success" if removed else "error",
            "message": "Folder removed from tracking." if removed else "Folder not found in tracked list.",
        })


# -------------------------------------------------------------------------
# Automated Rebuttal & Legal Reply Drafting Endpoint
# -------------------------------------------------------------------------

@app.route("/api/documents/<doc_id>/rebuttal", methods=["GET"])
def rebuttal_endpoint(doc_id: str):
    """Generates formal contract amendment/rebuttal letter addressing discrepancies."""
    doc = document_store.get(doc_id)
    doc_dict = doc.to_dict() if doc else None
    if not doc_dict:
        # Check catalog
        cat = catalog_mgr.get_all_documents()
        doc_dict = next((d for d in cat if d.get("doc_id") == doc_id), None)

    if not doc_dict:
        return jsonify({"status": "error", "message": f"Document ID '{doc_id}' not found."}), 404

    rebuttal_data = DocumentAnalyzer.draft_rebuttal_letter(doc_dict)
    return jsonify({
        "status": "success",
        "doc_id": doc_id,
        "rebuttal": rebuttal_data,
    })


# -------------------------------------------------------------------------
# Batch Master Dossier Export Endpoint
# -------------------------------------------------------------------------

@app.route("/api/documents/export-dossier", methods=["POST"])
def export_dossier_endpoint():
    """Compiles repository documents into compliance-ready .zip dossier."""
    data = request.get_json(silent=True) or {}
    docs = catalog_mgr.get_all_documents()
    if not docs:
        docs = [d.to_dict() for d in document_store.values()]

    if not docs:
        return jsonify({"status": "error", "message": "No documents in repository to bundle."}), 400

    output_dir = Path("vault/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = str(output_dir / f"dossier_{int(datetime.now().timestamp())}.zip")

    res = BatchDossierExporter.export_dossier(docs, zip_path)
    if res.get("success"):
        return jsonify({
            "status": "success",
            "message": "Dossier compiled successfully.",
            "export_details": res,
        })
    return jsonify({"status": "error", "message": res.get("error")}), 500


# -------------------------------------------------------------------------
# Automated Storage Retention Policy Endpoints
# -------------------------------------------------------------------------

@app.route("/api/retention/audit", methods=["GET"])
def retention_audit_endpoint():
    """Returns retention audit summary with archivable and shreddable counts."""
    docs = catalog_mgr.get_all_documents() or [d.to_dict() for d in document_store.values()]
    retention = RetentionPolicyManager()
    summary = retention.get_retention_summary(docs)
    return jsonify({
        "status": "success",
        "retention_summary": summary,
    })


@app.route("/api/retention/enforce", methods=["POST"])
def retention_enforce_endpoint():
    """Enforces auto-archival and DoD 5220.22-M secure shredding."""
    docs = catalog_mgr.get_all_documents() or [d.to_dict() for d in document_store.values()]
    retention = RetentionPolicyManager()
    result = retention.enforce_retention_policies(docs)
    return jsonify({
        "status": "success",
        "retention_result": result,
    })


# -------------------------------------------------------------------------
# Multi-Document Synthesis Endpoint
# -------------------------------------------------------------------------

@app.route("/api/ai/multi-synthesis", methods=["POST"])
def multi_synthesis_endpoint():
    """Synthesizes query answers across multiple related documents simultaneously."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "query is required."}), 400

    res = assistant.multi_document_synthesis(query)
    return jsonify(res)


def run_server(port: int = 5000, debug: bool = False):
    """Run Flask development server."""
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    run_server(port=5000, debug=True)
