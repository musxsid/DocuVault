"""
DocuVaultAI — Hybrid Storage Providers (Unit 1: OOP & Unit 2: APIs)
Implements an abstract BaseStorageProvider with concrete LocalStorageProvider
(using os/pathlib/shutil) and CloudStorageProvider (REST/HTTPS with offline mirror cache).
"""

import json
import os
import shutil
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from core.exceptions import (
    NetworkSyncError,
    StorageProviderError,
    StorageReadError,
    StorageWriteError,
)


class BaseStorageProvider(ABC):
    """Abstract Base Class for hybrid storage backends."""

    def __init__(self, name: str, base_dir: str) -> None:
        self.name: str = name
        self.base_dir: Path = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def list_files(self, subfolder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored documents and their metadata."""
        pass

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read binary content of a file."""
        pass

    @abstractmethod
    def save_file(self, relative_path: str, data: bytes) -> str:
        """Save binary content to storage. Returns the stored file path."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def get_metadata(self, relative_path: str) -> Dict[str, Any]:
        """Retrieve file metadata (size, timestamp, hash)."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if file exists in storage."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Direct laptop hard-drive storage provider utilizing os, pathlib, and shutil.
    Enables instant offline access with zero upload latency.
    """

    def __init__(self, root_dir: str = "vault/local") -> None:
        super().__init__(name="LocalStorageProvider", base_dir=root_dir)

    def _resolve(self, relative_path: str) -> Path:
        target = (self.base_dir / relative_path).resolve()
        # Ensure path traversal protection
        if not str(target).startswith(str(self.base_dir)):
            raise StorageProviderError(
                self.name,
                "resolve_path",
                f"Attempted path traversal attack: {relative_path}",
            )
        return target

    def list_files(self, subfolder: Optional[str] = None) -> List[Dict[str, Any]]:
        target_dir = self._resolve(subfolder) if subfolder else self.base_dir
        if not target_dir.exists():
            return []

        results: List[Dict[str, Any]] = []
        for path in target_dir.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.base_dir).as_posix()
                stat = path.stat()
                results.append({
                    "name": path.name,
                    "relative_path": rel_path,
                    "absolute_path": str(path),
                    "size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "provider": "Local Drive",
                    "synced": True,
                })
        return results

    def read_bytes(self, relative_path: str) -> bytes:
        target = self._resolve(relative_path)
        if not target.exists():
            raise StorageReadError(self.name, relative_path, "File does not exist.")
        try:
            with open(target, "rb") as f:
                return f.read()
        except Exception as e:
            raise StorageReadError(self.name, relative_path, str(e))

    def save_file(self, relative_path: str, data: bytes) -> str:
        target = self._resolve(relative_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as f:
                f.write(data)
            return str(target)
        except Exception as e:
            raise StorageWriteError(self.name, relative_path, str(e))

    def delete_file(self, relative_path: str) -> bool:
        target = self._resolve(relative_path)
        if not target.exists():
            return False
        try:
            target.unlink()
            return True
        except Exception as e:
            raise StorageProviderError(self.name, "delete_file", str(e))

    def get_metadata(self, relative_path: str) -> Dict[str, Any]:
        target = self._resolve(relative_path)
        if not target.exists():
            raise StorageReadError(self.name, relative_path, "File does not exist.")
        stat = target.stat()
        return {
            "name": target.name,
            "relative_path": relative_path,
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "provider": "Local Drive",
            "synced": True,
        }

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()


class CloudStorageProvider(BaseStorageProvider):
    """
    Cloud Storage Provider with HTTPS awareness and an offline local mirror cache.
    Seamlessly functions offline by falling back to the mirror, tracking sync status.
    """

    def __init__(
        self,
        endpoint_url: str = "https://mock-cloud.docuvault.internal/v1/storage",
        mirror_dir: str = "vault/cloud_mirror",
        api_token: Optional[str] = None,
    ) -> None:
        super().__init__(name="CloudStorageProvider", base_dir=mirror_dir)
        self.endpoint_url: str = endpoint_url
        self.api_token: Optional[str] = api_token or os.getenv("DOCUVAULT_CLOUD_TOKEN", "mock-token-xyz")
        self.is_online: bool = False
        self.sync_manifest_path: Path = self.base_dir / ".cloud_sync_manifest.json"
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self.sync_manifest_path.exists():
            try:
                with open(self.sync_manifest_path, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception:
                self.manifest = {}
        else:
            self.manifest = {}

    def _save_manifest(self) -> None:
        try:
            with open(self.sync_manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2)
        except Exception:
            pass

    def check_connection(self) -> bool:
        """Check cloud connectivity via REST ping with timeout."""
        try:
            # We perform a quick non-blocking health check with 1.5s timeout
            resp = requests.get(
                f"{self.endpoint_url}/health",
                timeout=1.5,
                headers={"Authorization": f"Bearer {self.api_token}"},
            )
            self.is_online = (resp.status_code == 200)
        except Exception:
            self.is_online = False
        return self.is_online

    def _resolve(self, relative_path: str) -> Path:
        target = (self.base_dir / relative_path).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise StorageProviderError(
                self.name,
                "resolve_path",
                f"Path traversal attack prevented: {relative_path}",
            )
        return target

    def list_files(self, subfolder: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists files from local mirror cache with sync state."""
        target_dir = self._resolve(subfolder) if subfolder else self.base_dir
        if not target_dir.exists():
            return []

        results: List[Dict[str, Any]] = []
        for path in target_dir.rglob("*"):
            if path.is_file() and path.name != ".cloud_sync_manifest.json":
                rel_path = path.relative_to(self.base_dir).as_posix()
                stat = path.stat()
                meta = self.manifest.get(rel_path, {})
                synced = meta.get("synced", False)

                results.append({
                    "name": path.name,
                    "relative_path": rel_path,
                    "absolute_path": str(path),
                    "size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "provider": "Cloud Vault",
                    "synced": synced,
                    "cloud_url": f"{self.endpoint_url}/{rel_path}",
                })
        return results

    def read_bytes(self, relative_path: str) -> bytes:
        """Read from cloud if online, otherwise seamlessly read from local offline mirror."""
        target = self._resolve(relative_path)

        # In offline-first design, read from mirror
        if target.exists():
            try:
                with open(target, "rb") as f:
                    return f.read()
            except Exception as e:
                raise StorageReadError(self.name, relative_path, str(e))

        # If not in mirror and online, try downloading
        if self.check_connection():
            try:
                resp = requests.get(
                    f"{self.endpoint_url}/{relative_path}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    self.save_file(relative_path, resp.content)
                    return resp.content
            except Exception as e:
                raise NetworkSyncError(self.endpoint_url, None, str(e))

        raise StorageReadError(
            self.name, relative_path, "File not present in mirror cache and cloud is offline."
        )

    def save_file(self, relative_path: str, data: bytes) -> str:
        """Save file to local offline mirror and mark for cloud synchronization."""
        target = self._resolve(relative_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as f:
                f.write(data)

            # Record in manifest
            self.manifest[relative_path] = {
                "synced": False,
                "last_modified": datetime.now().isoformat(),
                "size_bytes": len(data),
            }
            self._save_manifest()
            return str(target)
        except Exception as e:
            raise StorageWriteError(self.name, relative_path, str(e))

    def delete_file(self, relative_path: str) -> bool:
        target = self._resolve(relative_path)
        if target.exists():
            target.unlink()
            if relative_path in self.manifest:
                del self.manifest[relative_path]
                self._save_manifest()
            return True
        return False

    def get_metadata(self, relative_path: str) -> Dict[str, Any]:
        target = self._resolve(relative_path)
        if not target.exists():
            raise StorageReadError(self.name, relative_path, "File does not exist.")
        stat = target.stat()
        meta = self.manifest.get(relative_path, {})
        return {
            "name": target.name,
            "relative_path": relative_path,
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "provider": "Cloud Vault",
            "synced": meta.get("synced", False),
        }

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()
