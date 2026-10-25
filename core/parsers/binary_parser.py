"""
DocuVaultAI — Binary Parser & Integrity Engine (Unit 4: File Handling)
Inspects binary magic bytes in 'rb' mode to detect disguised/corrupted files,
and performs chunked cryptographic SHA-256 hashing for tamper detection.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from core.exceptions import CorruptFileError, TamperedFileError


class BinaryParser:
    """Validates file integrity using binary magic byte signatures and SHA-256 hashing."""

    # Magic byte signatures dictionary
    MAGIC_SIGNATURES: Dict[str, Tuple[bytes, ...]] = {
        ".pdf": (b"%PDF-",),
        ".xml": (b"<?xml", b"\xef\xbb\xbf<?xml", b"<invoice", b"<record", b"<document", b"<root"),
        ".zip": (b"PK\x03\x04",),
        ".docx": (b"PK\x03\x04",),
        ".xlsx": (b"PK\x03\x04",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".webp": (b"RIFF",),
    }

    # Dangerous signatures that should never be disguised as documents (e.g. Windows PE executables)
    DANGEROUS_SIGNATURES: Dict[str, bytes] = {
        "Windows Executable (MZ)": b"MZ",
        "ELF Binary": b"\x7fELF",
        "Mach-O Binary": b"\xfe\xed\xfa\xce",
    }

    @classmethod
    def read_magic_bytes(cls, filepath: str, num_bytes: int = 8) -> bytes:
        """Read the first N bytes of a file in raw binary 'rb' mode."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, "rb") as f:
            return f.read(num_bytes)

    @classmethod
    def calculate_sha256(cls, filepath: str, chunk_size: int = 65536) -> str:
        """Calculate SHA-256 hash in binary chunks (64KB) for memory-efficient cryptographic integrity."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def validate_file(cls, filepath: str, strict: bool = True) -> Dict[str, str]:
        """
        Validates file magic bytes and returns integrity report.
        Raises CorruptFileError if magic bytes do not match declared extension.
        """
        path = Path(filepath)
        ext = path.suffix.lower()
        magic = cls.read_magic_bytes(filepath, num_bytes=16)

        # Check for disguised malicious executables
        for name, sig in cls.DANGEROUS_SIGNATURES.items():
            if magic.startswith(sig):
                raise CorruptFileError(
                    filepath=filepath,
                    expected_format=ext,
                    found_magic=magic[:4],
                    reason=f"Dangerous executable format detected: {name}",
                )

        # Validate known document extensions
        if ext in cls.MAGIC_SIGNATURES:
            expected_sigs = cls.MAGIC_SIGNATURES[ext]
            matched = any(magic.startswith(sig) for sig in expected_sigs)
            if not matched:
                raise CorruptFileError(
                    filepath=filepath,
                    expected_format=ext,
                    found_magic=magic[:8],
                    reason=f"File extension is '{ext}' but binary magic bytes do not match expected signature.",
                )
        elif ext == ".txt":
            # For plain text, verify it can be decoded without null-byte binary corruption
            try:
                with open(filepath, "r", encoding="utf-8", errors="strict") as f:
                    sample = f.read(256)
                    if "\x00" in sample:
                        raise CorruptFileError(
                            filepath=filepath,
                            expected_format="text/plain",
                            found_magic=magic[:4],
                            reason="Binary null bytes found in plain text document.",
                        )
            except UnicodeDecodeError:
                # Try latin-1 fallback or raise
                try:
                    with open(filepath, "r", encoding="latin-1") as f:
                        sample = f.read(256)
                        if "\x00" in sample:
                            raise CorruptFileError(
                                filepath=filepath,
                                expected_format="text/plain",
                                found_magic=magic[:4],
                                reason="Binary null bytes found in plain text document.",
                            )
                except Exception as e:
                    raise CorruptFileError(
                        filepath=filepath,
                        expected_format="text/plain",
                        found_magic=magic[:4],
                        reason=f"Text decoding failed: {e}",
                    )

        sha256 = cls.calculate_sha256(filepath)
        size_bytes = os.path.getsize(filepath)

        return {
            "filepath": filepath,
            "filename": path.name,
            "extension": ext,
            "magic_hex": magic[:8].hex(),
            "sha256": sha256,
            "size_bytes": str(size_bytes),
            "status": "VALID",
        }

    @classmethod
    def verify_integrity(cls, filepath: str, expected_sha256: str) -> bool:
        """
        Verify that a file has not been altered or tampered with by comparing SHA-256.
        Raises TamperedFileError on mismatch.
        """
        actual_sha256 = cls.calculate_sha256(filepath)
        if actual_sha256.lower() != expected_sha256.lower():
            raise TamperedFileError(
                filepath=filepath,
                expected_hash=expected_sha256,
                actual_hash=actual_sha256,
            )
        return True
