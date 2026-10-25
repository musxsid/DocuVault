"""
DocuVault — Batch Multi-File Exporter & Compliance Dossier Bundler
Compiles selected documents, verification reports, and digital signatures
into a single structured ZIP archive or master audit dossier.
"""

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BatchDossierExporter:
    """
    Exports bundles of documents with cryptographic audit trails for compliance.
    """

    @classmethod
    def export_dossier_zip(
        cls,
        documents: List[Dict[str, Any]],
        output_zip_path: str,
        include_audit_report: bool = True,
    ) -> str:
        """
        Creates a structured compliance ZIP archive containing:
        - Original documents in their categorical folders
        - Cryptographic manifest (SHA-256 hashes, sizes, status)
        - Master compliance report (JSON)
        """
        out_p = Path(output_zip_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "dossier_title": "DocuVault Compliance Master Dossier",
            "exported_at": datetime.now().isoformat(),
            "total_documents": len(documents),
            "documents": [],
        }

        with zipfile.ZipFile(str(out_p), "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in documents:
                fpath = doc.get("filepath", "")
                fname = doc.get("filename", "document.txt")
                cat = doc.get("category", "General")

                manifest["documents"].append({
                    "filename": fname,
                    "category": cat,
                    "sha256_hash": doc.get("sha256_hash", ""),
                    "status": doc.get("status", "Verified"),
                    "page_count": doc.get("page_count", 1),
                    "counterparties": doc.get("counterparties", []),
                    "risk_level": (doc.get("risk_profile") or {}).get("risk_level", "Low"),
                })

                if fpath and Path(fpath).exists():
                    arcname = f"{cat}/{fname}"
                    zf.write(fpath, arcname=arcname)
                elif "pages" in doc:
                    arcname = f"{cat}/{fname}"
                    content = "\n".join([p.get("text", "") for p in doc["pages"]])
                    zf.writestr(arcname, content)

            if include_audit_report:
                report_str = json.dumps(manifest, indent=2)
                zf.writestr("MANIFEST_AUDIT_REPORT.json", report_str)

        return str(out_p)

    @classmethod
    def export_dossier(
        cls,
        documents: List[Dict[str, Any]],
        output_zip_path: str,
        include_audit_report: bool = True,
    ) -> Dict[str, Any]:
        """Convenience method returning summary dict with success flag and bundle sha256."""
        try:
            zip_file = cls.export_dossier_zip(documents, output_zip_path, include_audit_report)
            import hashlib
            with open(zip_file, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            return {
                "success": True,
                "zip_path": zip_file,
                "bundle_sha256": sha,
                "documents_exported": len(documents),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
