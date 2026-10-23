"""
DocuVaultAI — Automated File Sorter & Audit Logger (Unit 2: Automation & Logs)
Sorts incoming documents into categorical directories (/Legal, /Medical, /Academic,
/Financial, /General) based on binary validation and content analysis, recording
every operation in the persistent file_ops.log audit log.
"""

import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.base_document import DocumentFactory
from core.exceptions import CorruptFileError, InvalidFormError
from core.parsers.binary_parser import BinaryParser


class AuditLogger:
    """Thread-safe append-only logger for file sorting operations."""

    def __init__(self, log_path: str = "file_ops.log") -> None:
        self.log_path: Path = Path(log_path).resolve()
        self._lock = threading.Lock()

    def log_operation(
        self,
        level: str,
        action: str,
        filename: str,
        category: str,
        size_bytes: int,
        destination: str,
        extra: str = "",
    ) -> str:
        """
        Appends an operation entry to file_ops.log with format:
        [YYYY-MM-DD HH:MM:SS] LEVEL | ACTION | filename -> /Category/ | Size: N bytes | Dest: path
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{timestamp}] {level.upper():5} | {action.upper():6} | "
            f"{filename} \u2192 /{category}/ | Size: {size_bytes} bytes | Dest: {destination}"
        )
        if extra:
            entry += f" | {extra}"
        entry += "\n"

        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry)

        return entry.strip()

    def get_recent_logs(self, max_lines: int = 50) -> List[str]:
        """Read the most recent N lines from the operations log."""
        if not self.log_path.exists():
            return []
        with self._lock:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        return [line.strip() for line in lines[-max_lines:]]


class RegexFormValidator:
    """Regular Expression validator for document form fields and metadata."""

    EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$")
    ISO_DATE_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
    CURRENCY_PATTERN = re.compile(r"^[\$\€\£\₹]?\s*\d+(?:,\d{3})*(?:\.\d{2})?$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")

    @classmethod
    def validate_field(cls, field_name: str, value: str) -> bool:
        """Validates a single form field by name against its respective regex."""
        val = str(value).strip()
        field_lower = field_name.lower()

        if "email" in field_lower:
            if not cls.EMAIL_PATTERN.match(val):
                raise InvalidFormError(field_name, val, "user@domain.com")
        elif "date" in field_lower:
            if not cls.ISO_DATE_PATTERN.match(val):
                raise InvalidFormError(field_name, val, "YYYY-MM-DD")
        elif "amount" in field_lower or "price" in field_lower or "total" in field_lower:
            if not cls.CURRENCY_PATTERN.match(val):
                raise InvalidFormError(field_name, val, "$1,234.56 or 1234.56")
        elif "phone" in field_lower:
            if not cls.PHONE_PATTERN.match(val):
                raise InvalidFormError(field_name, val, "+1-234-567-8900")
        return True

    @classmethod
    def validate_form_payload(cls, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate entire dictionary payload of form inputs."""
        errors: List[str] = []
        for field, val in payload.items():
            try:
                cls.validate_field(field, str(val))
            except InvalidFormError as e:
                errors.append(str(e))
        return (len(errors) == 0, errors)


class FileOrganizerDaemon:
    """
    Automated sorting engine that categorizes files and files them into
    organized subdirectories while maintaining an audit log.
    """

    CATEGORIES = ["Legal", "Medical", "Academic", "Financial", "General"]

    def __init__(
        self,
        vault_root: str = "vault",
        log_file: str = "file_ops.log",
    ) -> None:
        self.vault_root: Path = Path(vault_root).resolve()
        self.logger: AuditLogger = AuditLogger(log_file)
        self._ensure_category_folders()

    def _ensure_category_folders(self) -> None:
        """Create category directories inside vault if they don't exist."""
        for cat in self.CATEGORIES:
            (self.vault_root / cat).mkdir(parents=True, exist_ok=True)
        (self.vault_root / "intake").mkdir(parents=True, exist_ok=True)
        (self.vault_root / "quarantine").mkdir(parents=True, exist_ok=True)

    def sort_file(self, filepath: str, copy_only: bool = False) -> Dict[str, Any]:
        """
        Sorts a single file:
        1. Validates magic byte integrity.
        2. Ingests via DocumentFactory to determine appropriate category.
        3. Moves (or copies) file to /vault/<Category>/<filename>.
        4. Logs operation in file_ops.log.
        """
        src_path = Path(filepath)
        if not src_path.exists():
            raise FileNotFoundError(f"File to sort does not exist: {filepath}")

        filename = src_path.name
        size_bytes = src_path.stat().st_size

        try:
            # Step 1: Magic byte validation
            BinaryParser.validate_file(str(src_path))

            # Step 2: Extract and categorize
            doc = DocumentFactory.create_document(str(src_path), enforce_magic_bytes=False)
            category = doc.get_category()

            # Step 3: Move to category destination folder
            dest_dir = self.vault_root / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename

            # Avoid overwriting identical name by suffixing if different content
            if dest_path.exists() and dest_path.resolve() != src_path.resolve():
                stem = src_path.stem
                ext = src_path.suffix
                dest_path = dest_dir / f"{stem}_{int(datetime.now().timestamp())}{ext}"

            if copy_only or src_path.resolve() == dest_path.resolve():
                if src_path.resolve() != dest_path.resolve():
                    shutil.copy2(src_path, dest_path)
            else:
                shutil.move(str(src_path), str(dest_path))

            # Step 4: Record audit log
            rel_dest = dest_path.relative_to(self.vault_root).as_posix()
            self.logger.log_operation(
                level="INFO",
                action="SORT",
                filename=filename,
                category=category,
                size_bytes=size_bytes,
                destination=f"vault/{rel_dest}",
                extra=f"SHA256: {doc.sha256_hash[:12]}...",
            )

            return {
                "success": True,
                "filename": filename,
                "category": category,
                "destination": str(dest_path),
                "doc_id": doc.doc_id,
                "status": "SORTED",
            }

        except CorruptFileError as e:
            # Move corrupt or disguised file to quarantine
            quarantine_dir = self.vault_root / "quarantine"
            dest_path = quarantine_dir / filename
            if not copy_only and src_path.resolve() != dest_path.resolve():
                shutil.move(str(src_path), str(dest_path))

            self.logger.log_operation(
                level="WARN",
                action="QUARANTINE",
                filename=filename,
                category="Quarantine",
                size_bytes=size_bytes,
                destination=f"vault/quarantine/{filename}",
                extra=f"Reason: {e.message}",
            )
            return {
                "success": False,
                "filename": filename,
                "category": "Quarantine",
                "error": e.message,
                "status": "QUARANTINED",
            }

    def process_intake_folder(self) -> List[Dict[str, Any]]:
        """Scans the vault/intake directory and automatically sorts all pending files."""
        intake_dir = self.vault_root / "intake"
        results = []
        for file in intake_dir.iterdir():
            if file.is_file():
                res = self.sort_file(str(file), copy_only=False)
                results.append(res)
        return results
