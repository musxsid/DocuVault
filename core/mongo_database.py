"""
DocuVault — Real-time MongoDB Database Layer
Provides live MongoDB persistence for documents, audit trails, version histories,
and compliance deadline tracking.
"""

import os
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class MongoDatabase:
    """
    Real-time MongoDB manager for DocuVaultAI.
    Connects to local or remote MongoDB instance, persisting document metadata,
    extracted clauses, audit trail records, version histories, and deadlines.
    """

    def __init__(self, uri: Optional[str] = None, db_name: str = "docuvault_db") -> None:
        self.uri = uri or os.getenv("DOCUVAULT_MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = db_name
        self.client: Optional[pymongo.MongoClient] = None
        self.db = None
        self._connected = False
        self._memory_backup: Dict[str, Dict[str, Any]] = {}
        self._audit_backup: List[Dict[str, Any]] = []
        self._versions_backup: Dict[str, List[Dict[str, Any]]] = {}
        self._deadlines_backup: List[Dict[str, Any]] = []

        self._connect()

    def _connect(self) -> bool:
        try:
            self.client = pymongo.MongoClient(
                self.uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000
            )
            # Force server ping to verify actual connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self._connected = True

            # Ensure indexes for performance
            self.db.documents.create_index("doc_id", unique=True)
            self.db.documents.create_index("sha256_hash")
            self.db.documents.create_index("category")
            self.db.documents.create_index("owner_email")
            self.db.audit_logs.create_index("timestamp")
            self.db.audit_logs.create_index("owner_email")
            self.db.versions.create_index([("doc_id", 1), ("version_number", -1)])
            self.db.deadlines.create_index("due_date")

            return True
        except Exception:
            self._connected = False
            self.client = None
            self.db = None
            return False

    @property
    def is_connected(self) -> bool:
        """Returns True if connected to live MongoDB server."""
        if not self._connected or not self.client:
            return self._connect()
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            self._connected = False
            return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DOCUMENT CRUD OPERATIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def save_document(self, doc_dict: Dict[str, Any], user_email: Optional[str] = None) -> bool:
        """Saves or updates a document record in MongoDB with user ownership scoping."""
        doc_id = doc_dict.get("doc_id")
        if not doc_id:
            return False

        record = dict(doc_dict)
        owner = user_email or record.get("owner_email")
        if owner:
            record["owner_email"] = str(owner).strip().lower()

        record["updated_at"] = datetime.now().isoformat()
        if "created_at" not in record:
            record["created_at"] = datetime.now().isoformat()

        if self.is_connected:
            try:
                self.db.documents.update_one(
                    {"doc_id": doc_id},
                    {"$set": record},
                    upsert=True
                )
                self.log_audit("DB_SAVE", f"Document '{record.get('filename')}' saved to MongoDB", doc_id, user_email=record.get("owner_email"))
                return True
            except Exception as e:
                print(f"[MongoDatabase] Save error: {e}")

        # Fallback to in-memory cache
        self._memory_backup[doc_id] = record
        return True

    SIDDHARTH_ALIASES = [
        "siddharth.workspace@gmail.com",
        "musxsid@gmail.com",
        "siddharth",
        "sid",
        "siddharth shakyawal",
        "siddharth.shakyawal",
        "user@docuvault.local",
        "demo@docuvault.ai",
    ]

    @classmethod
    def _is_siddharth_alias(cls, email_or_name: Optional[str]) -> bool:
        if not email_or_name:
            return False
        clean = str(email_or_name).strip().lower()
        if clean in cls.SIDDHARTH_ALIASES:
            return True
        return any(a in clean for a in ["siddharth", "musxsid", "sid"])

    @classmethod
    def _match_owner_query(cls, user_email: Optional[str]) -> Optional[Any]:
        if not user_email:
            return None
        clean = str(user_email).strip().lower()
        if cls._is_siddharth_alias(clean):
            return {"$in": cls.SIDDHARTH_ALIASES}
        return clean

    @classmethod
    def _matches_owner(cls, doc_owner: Optional[str], user_email: Optional[str]) -> bool:
        if not user_email:
            return True
        u_clean = str(user_email).strip().lower()
        d_clean = (doc_owner or "").strip().lower()
        if cls._is_siddharth_alias(u_clean):
            return cls._is_siddharth_alias(d_clean) or d_clean in ("", "user@docuvault.local")
        return d_clean == u_clean

    def insert_document(self, doc_dict: Dict[str, Any], user_email: Optional[str] = None) -> bool:
        """Alias for save_document to support insert semantics."""
        return self.save_document(doc_dict, user_email=user_email)

    def get_document(self, doc_id: str, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single document by doc_id, optionally ensuring user ownership."""
        if self.is_connected:
            try:
                q: Dict[str, Any] = {"doc_id": doc_id}
                if user_email:
                    q["owner_email"] = self._match_owner_query(user_email)
                doc = self.db.documents.find_one(q, {"_id": 0})
                if doc:
                    return doc
            except Exception:
                pass
        doc = self._memory_backup.get(doc_id)
        if doc and user_email:
            if not self._matches_owner(doc.get("owner_email"), user_email):
                return None
        return doc

    def list_documents(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists documents from MongoDB, optionally filtered by category, search query, and user_email."""
        if self.is_connected:
            try:
                q: Dict[str, Any] = {}
                if user_email:
                    q["owner_email"] = self._match_owner_query(user_email)
                if category and category != "All":
                    q["category"] = category
                if search_query:
                    regex = {"$regex": search_query, "$options": "i"}
                    q["$or"] = [
                        {"filename": regex},
                        {"category": regex},
                        {"sha256_hash": regex},
                    ]
                docs = list(self.db.documents.find(q, {"_id": 0}).sort("created_at", -1))
                return docs
            except Exception as e:
                print(f"[MongoDatabase] List error: {e}")

        # Fallback to in-memory backup
        res = list(self._memory_backup.values())
        if user_email:
            res = [d for d in res if self._matches_owner(d.get("owner_email"), user_email)]
        if category and category != "All":
            res = [d for d in res if d.get("category") == category]
        if search_query:
            sq = search_query.lower()
            res = [d for d in res if sq in d.get("filename", "").lower() or sq in d.get("category", "").lower()]
        return res

    def delete_document(self, doc_id: str, user_email: Optional[str] = None) -> bool:
        """Deletes a document from MongoDB collection."""
        if self.is_connected:
            try:
                del_q: Dict[str, Any] = {"doc_id": doc_id}
                if user_email:
                    del_q["owner_email"] = self._match_owner_query(user_email)
                self.db.documents.delete_one(del_q)
                self.log_audit("DB_DELETE", f"Document doc_id={doc_id} deleted from MongoDB", doc_id, user_email=user_email)
            except Exception as e:
                print(f"[MongoDatabase] Delete error: {e}")

        if doc_id in self._memory_backup:
            if not user_email or self._matches_owner(self._memory_backup[doc_id].get("owner_email"), user_email):
                del self._memory_backup[doc_id]
        return True

    def update_document_status(self, doc_id: str, status: str) -> bool:
        """Updates document verification/integrity status."""
        if self.is_connected:
            try:
                self.db.documents.update_one(
                    {"doc_id": doc_id},
                    {"$set": {"status": status, "status_updated_at": datetime.now().isoformat()}}
                )
                self.log_audit("STATUS_UPDATE", f"Document status changed to '{status}'", doc_id)
                return True
            except Exception:
                pass

        if doc_id in self._memory_backup:
            self._memory_backup[doc_id]["status"] = status
            return True
        return False

    def find_by_hash(self, sha256_hash: str, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Finds any document matching the specified SHA-256 cryptographic hash."""
        if not sha256_hash:
            return None
        if self.is_connected:
            try:
                q: Dict[str, Any] = {"sha256_hash": sha256_hash}
                if user_email:
                    q["owner_email"] = self._match_owner_query(user_email)
                doc = self.db.documents.find_one(q, {"_id": 0})
                if doc:
                    return doc
            except Exception:
                pass

        for d in self._memory_backup.values():
            if d.get("sha256_hash") == sha256_hash:
                if not user_email or self._matches_owner(d.get("owner_email"), user_email):
                    return d
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AUDIT TRAIL LOGGING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def log_audit(self, action: str, details: str, doc_id: Optional[str] = None, operator: str = "System", user_email: Optional[str] = None) -> None:
        """Logs an immutable event into MongoDB audit_logs collection."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "doc_id": doc_id,
            "operator": operator,
            "owner_email": user_email.strip().lower() if user_email else None,
        }
        if self.is_connected:
            try:
                self.db.audit_logs.insert_one(entry)
                return
            except Exception:
                pass
        self._audit_backup.append(entry)

    def get_audit_logs(self, limit: int = 100, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent audit logs ordered by timestamp descending, optionally filtered by user."""
        if self.is_connected:
            try:
                q: Dict[str, Any] = {}
                if user_email:
                    q["owner_email"] = self._match_owner_query(user_email)
                return list(self.db.audit_logs.find(q, {"_id": 0}).sort("timestamp", -1).limit(limit))
            except Exception:
                pass
        logs = self._audit_backup
        if user_email:
            logs = [e for e in logs if e.get("owner_email", "").strip().lower() == user_email.strip().lower()]
        return list(reversed(logs[-limit:]))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DOCUMENT VERSION HISTORY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def save_version(self, doc_id: str, version_dict: Dict[str, Any]) -> None:
        """Saves a version snapshot for a document."""
        version_dict["doc_id"] = doc_id
        if "created_at" not in version_dict:
            version_dict["created_at"] = datetime.now().isoformat()

        if self.is_connected:
            try:
                self.db.versions.insert_one(version_dict)
                self.log_audit("VERSION_CREATE", f"Version {version_dict.get('version_number')} saved", doc_id)
                return
            except Exception:
                pass

        if doc_id not in self._versions_backup:
            self._versions_backup[doc_id] = []
        self._versions_backup[doc_id].append(version_dict)

    def get_versions(self, doc_id: str) -> List[Dict[str, Any]]:
        """Retrieves all versions for a document."""
        if self.is_connected:
            try:
                vers = list(self.db.versions.find({"doc_id": doc_id}, {"_id": 0}).sort("version_number", -1))
                if vers:
                    return vers
            except Exception:
                pass
        return self._versions_backup.get(doc_id, [])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SMART DEADLINES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def save_deadline(self, deadline: Dict[str, Any], user_email: Optional[str] = None) -> None:
        """Saves or updates a deadline."""
        d_id = deadline.get("id") or str(len(self._deadlines_backup) + 1)
        deadline["id"] = d_id
        if user_email:
            deadline["owner_email"] = user_email.strip().lower()
        if self.is_connected:
            try:
                self.db.deadlines.update_one({"id": d_id}, {"$set": deadline}, upsert=True)
                return
            except Exception:
                pass

        # Update in backup
        existing = [i for i, d in enumerate(self._deadlines_backup) if d.get("id") == d_id]
        if existing:
            self._deadlines_backup[existing[0]] = deadline
        else:
            self._deadlines_backup.append(deadline)

    def list_deadlines(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all document deadlines."""
        if self.is_connected:
            try:
                q: Dict[str, Any] = {}
                if user_email:
                    q["$or"] = [{"owner_email": user_email.strip().lower()}, {"owner_email": {"$exists": False}}]
                items = list(self.db.deadlines.find(q, {"_id": 0}).sort("due_date", 1))
                return items
            except Exception:
                pass

        items = self._deadlines_backup
        if user_email:
            items = [d for d in items if not d.get("owner_email") or d.get("owner_email") == user_email.strip().lower()]
        return list(items)

    def purge_all_data(self) -> None:
        """Purges all documents, audit logs, versions, and deadlines for a fresh vault state."""
        if self.is_connected:
            try:
                self.db.documents.delete_many({})
                self.db.audit_logs.delete_many({})
                self.db.versions.delete_many({})
                self.db.deadlines.delete_many({})
            except Exception as e:
                print(f"[MongoDatabase] Purge error: {e}")
        self._memory_backup.clear()
        self._audit_backup.clear()
        self._versions_backup.clear()
        self._deadlines_backup.clear()

    def _seed_default_deadlines(self):
        """Seeds realistic initial deadline reminders for the demo."""
        today = date.today()
        sample_deadlines = [
            {
                "id": "DL-101",
                "title": "Vendor Invoice Payment Due (INV-9042)",
                "document": "Vendor_Invoice_INV-9042.xml",
                "category": "Financial",
                "due_date": (today + timedelta(days=2)).isoformat(),
                "priority": "High",
                "status": "Upcoming",
                "reminder_days": [7, 3, 1],
                "notes": "Net-30 vendor invoice payment for IT Infrastructure Services.",
            },
            {
                "id": "DL-102",
                "title": "Master Services Agreement Renewal Notice",
                "document": "Master_Services_Agreement_NY.txt",
                "category": "Legal",
                "due_date": (today + timedelta(days=14)).isoformat(),
                "priority": "Medium",
                "status": "Upcoming",
                "reminder_days": [30, 14, 7],
                "notes": "30-day non-renewal clause window.",
            },
            {
                "id": "DL-103",
                "title": "Apex Quantum NDA Expiration Window",
                "document": "NDA_Apex_Quantum_2026.pdf",
                "category": "Legal",
                "due_date": (today + timedelta(days=28)).isoformat(),
                "priority": "Normal",
                "status": "On Track",
                "reminder_days": [30, 7],
                "notes": "Annual bilateral confidentiality term completion.",
            },
            {
                "id": "DL-104",
                "title": "Quarterly HIPAA Patient Record Audit",
                "document": "Medical_Clinical_Record_MRN77821.xml",
                "category": "Medical",
                "due_date": (today - timedelta(days=1)).isoformat(),
                "priority": "Critical",
                "status": "Overdue",
                "reminder_days": [7, 3, 1],
                "notes": "Routine statutory compliance verification check.",
            },
        ]
        for d in sample_deadlines:
            self.save_deadline(d)

    def close(self):
        """Safely close client connections."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.db = None
            self._connected = False
