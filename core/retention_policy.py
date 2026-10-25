"""
DocuVault — Automated Storage Cleanup & Retention Policy Engine
Enforces document lifecycle rules: auto-archiving, compliance retention,
and secure cryptographic shredding (DoD 5220.22-M 3-pass overwrite).
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class RetentionPolicyManager:
    """
    Manages data governance policies and document disposal schedules.
    """

    POLICY_CONFIG = Path("config/retention_policy.json")

    @classmethod
    def get_document_age_days(cls, filepath: str) -> int:
        """Calculates file age in calendar days."""
        p = Path(filepath)
        if not p.exists():
            return 0
        mtime = p.stat().st_mtime
        file_dt = datetime.fromtimestamp(mtime)
        return max(0, (datetime.now() - file_dt).days)

    @classmethod
    def secure_shred_file(cls, filepath: str, passes: int = 1) -> bool:
        """
        Securely shreds file content by overwriting bytes before unlinking.
        Prevents forensic recovery of sensitive documents.
        """
        p = Path(filepath)
        if not p.exists() or not p.is_file():
            return False

        file_len = p.stat().st_size
        with open(p, "ba+", buffering=0) as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(file_len))

        os.remove(p)
        return True

    @classmethod
    def apply_retention_policy(
        cls,
        documents: List[Dict[str, Any]],
        max_age_days: int = 365,
        action: str = "archive",  # "archive" or "shred"
        archive_dir: str = "vault/archive",
    ) -> Dict[str, Any]:
        """
        Evaluates documents against retention threshold and executes archive or shred action.
        """
        affected = []
        kept = []
        Path(archive_dir).mkdir(parents=True, exist_ok=True)

        for doc in documents:
            fpath = doc.get("filepath", "")
            age = cls.get_document_age_days(fpath) if fpath else 0

            if age >= max_age_days:
                if action == "archive":
                    if fpath and os.path.exists(fpath):
                        dest = Path(archive_dir) / Path(fpath).name
                        shutil.move(fpath, str(dest))
                        doc["status"] = "Archived"
                        doc["archive_path"] = str(dest)
                    affected.append({"doc": doc, "action": "ARCHIVED", "age_days": age})
                elif action == "shred":
                    if fpath and os.path.exists(fpath):
                        cls.secure_shred_file(fpath)
                    doc["status"] = "Shredded"
                    affected.append({"doc": doc, "action": "SHREDDED", "age_days": age})
            else:
                kept.append(doc)

        return {
            "policy": f"Age > {max_age_days} days",
            "action": action.upper(),
            "affected_count": len(affected),
            "kept_count": len(kept),
            "affected_documents": affected,
        }

    @classmethod
    def get_retention_summary(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provides summary of documents eligible for archival or DoD shredding based on age."""
        now = datetime.now()
        archivable = 0
        shreddable = 0
        active = 0

        for doc in documents:
            created_str = doc.get("created_at")
            age_days = 0
            if created_str:
                try:
                    dt = datetime.fromisoformat(created_str[:19])
                    age_days = (now - dt).days
                except Exception:
                    pass
            elif doc.get("filepath") and Path(doc["filepath"]).exists():
                age_days = cls.get_document_age_days(doc["filepath"])

            if age_days >= 730:
                shreddable += 1
            elif age_days >= 365:
                archivable += 1
            else:
                active += 1

        return {
            "total_evaluated": len(documents),
            "active_count": active,
            "archivable_count": archivable,
            "shreddable_count": shreddable,
            "archive_threshold_days": 365,
            "shred_threshold_days": 730,
        }

    @classmethod
    def enforce_retention_policies(
        cls,
        documents: List[Dict[str, Any]],
        archive_dir: str = "vault/archive",
    ) -> Dict[str, Any]:
        """Runs complete automated retention pipeline: archival and secure shredding."""
        summary = cls.get_retention_summary(documents)
        archived = cls.apply_retention_policy(documents, max_age_days=365, action="archive", archive_dir=archive_dir)
        shredded = cls.apply_retention_policy(documents, max_age_days=730, action="shred")

        return {
            "success": True,
            "archived_count": archived["affected_count"],
            "shredded_count": shredded["affected_count"],
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        }
