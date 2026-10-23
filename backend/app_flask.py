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
from core.base_document import BaseDocument, DocumentFactory
from core.catalog_manager import CatalogManager
from core.exceptions import CorruptFileError, DocuVaultError, TamperedFileError
from core.organizer import FileOrganizerDaemon
from core.parsers.binary_parser import BinaryParser
from core.storage_providers import CloudStorageProvider, LocalStorageProvider
from core.vector_search import VectorSearchEngine

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
        if new_mode in ["Local Drive", "Cloud Vault"]:
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

    if not query:
        return jsonify({"status": "error", "message": "Query parameter cannot be empty."}), 400

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


def run_server(port: int = 5000, debug: bool = False):
    """Run Flask development server."""
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    run_server(port=5000, debug=True)
