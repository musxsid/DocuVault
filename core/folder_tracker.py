"""
DocuVault — Real-Time Directory Tracker & Git-Like Folder Synchronizer
Tracks one or more user-selected directories for newly dropped or modified files,
automatically runs binary validation, OCR, cryptographic hashing, and semantic indexing.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from core.base_document import DocumentFactory
from core.document_analyzer import DocumentAnalyzer
from core.ocr_engine import OCREngine
from core.organizer import AuditLogger
from core.parsers.binary_parser import BinaryParser


class DirectoryTracker:
    """
    Git-like folder watcher and automatic ingestion engine.
    Maintains a persistent index of tracked folders and file modification states.
    """

    CONFIG_FILE = Path("config/watched_folders.json")
    INDEX_FILE = Path("config/tracked_files_index.json")
    SUPPORTED_EXTENSIONS = {".pdf", ".xml", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".docx"}

    def __init__(
        self,
        on_document_discovered: Optional[Callable[[Dict[str, Any]], None]] = None,
        mongo: Optional[Any] = None,
        owner_email: Optional[str] = None,
    ) -> None:
        self._ensure_config_dir()
        self.on_document_discovered = on_document_discovered
        self.owner_email = owner_email.strip().lower() if owner_email else None
        self.audit_logger = AuditLogger("file_ops.log")
        self._watched_folders: List[str] = self._load_watched_folders()
        self._file_index: Dict[str, Dict[str, Any]] = self._load_file_index()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        try:
            from core.mongo_database import MongoDatabase
            self.mongo = mongo or MongoDatabase()
        except Exception:
            self.mongo = None

    def set_owner_email(self, email: Optional[str]) -> None:
        """Sets or updates the active user email for tagging discovered documents."""
        with self._lock:
            self.owner_email = email.strip().lower() if email else None

    def _ensure_config_dir(self) -> None:
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_watched_folders(self) -> List[str]:
        if not self.CONFIG_FILE.exists():
            return []
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [os.path.abspath(p) for p in data if os.path.exists(p)]
        except Exception:
            return []

    def _save_watched_folders(self) -> None:
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._watched_folders, f, indent=2)

    def _load_file_index(self) -> Dict[str, Dict[str, Any]]:
        if not self.INDEX_FILE.exists():
            return {}
        try:
            with open(self.INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_file_index(self) -> None:
        with open(self.INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(self._file_index, f, indent=2)

    def get_watched_folders(self) -> List[str]:
        """Returns the list of currently monitored directory paths."""
        with self._lock:
            return list(self._watched_folders)

    def add_watched_folder(self, folder_path: str) -> bool:
        """Adds a folder to tracking and initiates an immediate discovery scan."""
        abs_p = os.path.abspath(folder_path)
        if not os.path.isdir(abs_p):
            return False

        with self._lock:
            if abs_p not in self._watched_folders:
                self._watched_folders.append(abs_p)
                self._save_watched_folders()
                return True
        return False

    def remove_watched_folder(self, folder_path: str) -> bool:
        """Removes a folder from tracking."""
        abs_p = os.path.abspath(folder_path)
        with self._lock:
            if abs_p in self._watched_folders:
                self._watched_folders.remove(abs_p)
                self._save_watched_folders()
                return True
        return False

    def process_file(self, filepath: str, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Parses, validates, hashes, OCRs, and enriches a discovered document.
        """
        p = Path(filepath)
        if not p.exists() or p.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return None

        stat = p.stat()
        mtime = stat.st_mtime
        size = stat.st_size

        try:
            # 1. Binary validation & SHA-256
            BinaryParser.validate_file(str(p))
            sha256 = BinaryParser.calculate_sha256(str(p))

            # 2. Check if already indexed with matching hash and mtime
            indexed_entry = self._file_index.get(str(p))
            if indexed_entry and indexed_entry.get("sha256") == sha256 and indexed_entry.get("mtime") == mtime and not force:
                if self.mongo and self.owner_email:
                    existing = self.mongo.find_by_hash(sha256, user_email=self.owner_email)
                    if existing:
                        return None  # Unchanged and already saved for this user
                else:
                    return None  # Unchanged

            # If force is requested and document already exists in MongoDB for this user, reuse it
            if force and self.mongo and self.owner_email:
                existing = self.mongo.find_by_hash(sha256, user_email=self.owner_email)
                if existing:
                    return existing

            # 3. Text Extraction with OCR fallback for images/scans
            is_image = p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]
            if is_image:
                ocr_res = OCREngine.extract_text_from_image(str(p))
                raw_text = ocr_res.get("text", "")
                pages = ocr_res.get("pages", [{"page_number": 1, "text": raw_text}])
                doc = DocumentFactory.create_document(
                    filepath=str(p),
                    raw_text=raw_text,
                    enforce_magic_bytes=False,
                )
                doc_dict = doc.to_dict()
                doc_dict["pages"] = pages
                doc_dict["ocr_extracted"] = True
                doc_dict["ocr_confidence"] = ocr_res.get("confidence", 95.0)
                doc_dict["ocr_engine"] = ocr_res.get("engine", "DocuVault Hybrid OCR")
                if doc_dict.get("category") == "Generic":
                    doc_dict["category"] = "Images"
            else:
                doc = DocumentFactory.create_document(
                    filepath=str(p),
                    enforce_magic_bytes=False,
                )
                doc_dict = doc.to_dict()

            # 4. Intelligence Enrichment: Summary, Counterparties, Risk Badge
            full_text = " ".join([page.get("text", "") for page in doc_dict.get("pages", [])]) or doc_dict.get("raw_text", "")
            doc_dict["executive_summary"] = DocumentAnalyzer.extract_executive_summary(full_text, doc.filename)
            doc_dict["counterparties"] = DocumentAnalyzer.extract_counterparties(full_text)
            doc_dict["risk_profile"] = DocumentAnalyzer.calculate_risk_profile(full_text, doc_dict.get("clauses"))
            doc_dict["tracked_folder"] = str(p.parent)
            doc_dict["discovered_at"] = datetime.now().isoformat()
            if self.owner_email:
                doc_dict["owner_email"] = self.owner_email
            if "created_at" not in doc_dict:
                doc_dict["created_at"] = datetime.now().isoformat()
            doc_dict["updated_at"] = datetime.now().isoformat()

            # 5. Persist Document-Wise in MongoDB Real-Time Layer
            if self.mongo:
                try:
                    self.mongo.save_document(doc_dict, user_email=self.owner_email)
                except Exception as me:
                    print(f"[DirectoryTracker] MongoDB auto-save notice: {me}")

            # 6. Update index
            with self._lock:
                self._file_index[str(p)] = {
                    "sha256": sha256,
                    "mtime": mtime,
                    "size": size,
                    "doc_id": doc.doc_id,
                    "filename": doc.filename,
                    "indexed_at": datetime.now().isoformat(),
                }
                self._save_file_index()

            # 7. Audit Logging to file_ops.log
            try:
                self.audit_logger.log_operation(
                    level="INFO",
                    action="TRACK_DISCOVER",
                    filename=doc.filename,
                    category=doc_dict.get("category", doc.get_category()),
                    size_bytes=size,
                    destination=str(p),
                    extra=f"SHA256: {sha256[:12]}... | Risk: {doc_dict.get('risk_profile', {}).get('risk_badge', 'Low')}",
                )
            except Exception:
                pass

            return doc_dict

        except Exception as e:
            # Skip invalid or corrupt temp files gracefully
            print(f"[DirectoryTracker] Warning parsing file '{p.name}': {e}")
            return None

    def scan_folder(self, folder_path: str, force: bool = False) -> List[Dict[str, Any]]:
        """Scans a single watched directory and processes any new or modified files."""
        abs_p = os.path.abspath(folder_path)
        if not os.path.isdir(abs_p):
            return []

        discovered = []
        try:
            for root, _, files in os.walk(abs_p):
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        fpath = os.path.join(root, f)
                        res = self.process_file(fpath, force=force)
                        if res:
                            discovered.append(res)
                            if self.on_document_discovered:
                                self.on_document_discovered(res)
        except Exception:
            pass

        return discovered

    def scan_all_watched(self, force: bool = False) -> List[Dict[str, Any]]:
        """Scans all tracked directories for changes."""
        all_discovered = []
        for folder in self.get_watched_folders():
            discovered = self.scan_folder(folder, force=force)
            all_discovered.extend(discovered)
        return all_discovered

    def start_background_monitoring(self, poll_interval_sec: float = 3.0) -> None:
        """Starts background daemon thread that continually monitors folders."""
        if self._running:
            return
        self._running = True

        def _monitor_loop():
            while self._running:
                try:
                    self.scan_all_watched()
                except Exception:
                    pass
                time.sleep(poll_interval_sec)

        self._thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._thread.start()

    def stop_background_monitoring(self) -> None:
        """Terminates background monitor thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
