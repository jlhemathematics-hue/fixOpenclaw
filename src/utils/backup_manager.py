"""
BackupManager - OpenClaw Configuration Backup & Restore

Manages real backups of OpenClaw config files and supports
one-command restore to the latest (or any) backup.
"""

import os
import shutil
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class BackupManager:
    """
    Real backup/restore manager for OpenClaw configuration files.

    Features:
    - Create timestamped backups before any repair
    - List all available backups with metadata
    - Restore the latest backup (or any specific one) in one call
    - Verify backup integrity via SHA-256 checksums
    - Auto-prune old backups according to retention policy
    """

    MANIFEST_FILE = "manifest.json"

    def __init__(self, backup_dir: str = "backups", retention_days: int = 7):
        """
        Args:
            backup_dir: Root directory where backups are stored.
            retention_days: Backups older than this are pruned automatically.
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(
        self,
        source_paths: List[str],
        label: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Backup a list of files/directories.

        Args:
            source_paths: Absolute or relative paths to back up.
            label: Optional human-readable label (e.g. repair_id).
            metadata: Extra info stored in the manifest (anomaly type, etc.).

        Returns:
            Dict with backup_id, path, files_backed_up, checksums.
        """
        # BUG FIX 1: Validate that source_paths is non-empty before creating
        # a backup directory.  An empty backup is not meaningful and should
        # be rejected immediately so callers don't assume a no-op backup
        # succeeded.
        if not source_paths:
            return {
                "success": False,
                "backup_id": None,
                "backup_path": None,
                "files_backed_up": 0,
                "errors": ["source_paths is empty — nothing to back up"],
                "manifest": None,
            }

        # BUG FIX 2: Use microseconds + a short UUID fragment to make the
        # backup_id unique even when two backups are created within the same
        # second.  Previously, same-second calls produced identical IDs,
        # causing the second backup directory to silently overwrite the first
        # backup's manifest file while leaving orphaned files on disk.
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        unique_tag = uuid.uuid4().hex[:6]
        backup_id = f"backup_{ts}_{unique_tag}" + (f"_{label}" if label else "")
        dest = self.backup_dir / backup_id
        dest.mkdir(parents=True, exist_ok=True)

        backed_up: List[str] = []
        checksums: Dict[str, str] = {}
        errors: List[str] = []

        for src in source_paths:
            src_path = Path(src)
            if not src_path.exists():
                errors.append(f"Source not found: {src}")
                continue
            try:
                rel = src_path.name
                dst = dest / rel
                if src_path.is_dir():
                    shutil.copytree(src_path, dst)
                else:
                    shutil.copy2(src_path, dst)
                backed_up.append(str(src_path))
                checksums[str(src_path)] = self._sha256(dst if dst.is_file() else None)
            except Exception as exc:
                errors.append(f"{src}: {exc}")

        manifest = {
            "backup_id": backup_id,
            "created_at": datetime.now().isoformat(),
            "label": label,
            "source_paths": source_paths,
            "files_backed_up": backed_up,
            "checksums": checksums,
            "errors": errors,
            "metadata": metadata or {},
        }
        (dest / self.MANIFEST_FILE).write_text(json.dumps(manifest, indent=2))

        # BUG FIX 1 (continued): success requires at least one file to have
        # been backed up AND no errors.  Previously success=True when all
        # source files were missing (errors list populated, backed_up empty).
        return {
            "success": len(errors) == 0 and len(backed_up) > 0,
            "backup_id": backup_id,
            "backup_path": str(dest),
            "files_backed_up": len(backed_up),
            "errors": errors,
            "manifest": manifest,
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Return all backups sorted newest-first.

        Each entry contains the full manifest plus a 'backup_path' key.
        """
        backups = []
        for entry in sorted(self.backup_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue
            manifest_path = entry / self.MANIFEST_FILE
            if not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text())
                manifest["backup_path"] = str(entry)
                backups.append(manifest)
            except Exception:
                pass
        return backups

    def get_latest_backup(self) -> Optional[Dict[str, Any]]:
        """Return the most recent backup manifest, or None if no backups exist."""
        backups = self.list_backups()
        return backups[0] if backups else None

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Return a specific backup by ID, or None."""
        dest = self.backup_dir / backup_id
        manifest_path = dest / self.MANIFEST_FILE
        if not manifest_path.exists():
            return None
        manifest = json.loads(manifest_path.read_text())
        manifest["backup_path"] = str(dest)
        return manifest

    def restore_backup(
        self,
        backup_id: Optional[str] = None,
        verify_checksums: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore a backup.

        Args:
            backup_id: ID of backup to restore. If None, restores the latest.
            verify_checksums: Validate SHA-256 before restoring each file.
            dry_run: If True, only simulate the restore (no files changed).

        Returns:
            Dict with success flag, restored files, and any errors.
        """
        # Resolve which backup to use
        if backup_id:
            manifest = self.get_backup(backup_id)
            if manifest is None:
                return {
                    "success": False,
                    "error": f"Backup not found: {backup_id}",
                    "restored_files": [],
                }
        else:
            manifest = self.get_latest_backup()
            if manifest is None:
                return {
                    "success": False,
                    "error": "No backups available to restore.",
                    "restored_files": [],
                }

        backup_path = Path(manifest["backup_path"])
        source_paths = manifest.get("source_paths", [])
        stored_checksums = manifest.get("checksums", {})

        restored: List[str] = []
        errors: List[str] = []

        for src_str in source_paths:
            src_original = Path(src_str)
            # The backed-up copy lives under backup_path/<filename>
            backed_copy = backup_path / src_original.name

            if not backed_copy.exists():
                errors.append(f"Backup copy missing: {backed_copy}")
                continue

            # Checksum verification
            if verify_checksums and backed_copy.is_file():
                expected = stored_checksums.get(src_str)
                actual = self._sha256(backed_copy)
                if expected and actual != expected:
                    errors.append(
                        f"Checksum mismatch for {src_str}: "
                        f"expected {expected[:8]}… got {actual[:8]}…"
                    )
                    continue

            if dry_run:
                restored.append(f"[DRY-RUN] Would restore: {src_str}")
                continue

            try:
                # Ensure parent directory exists
                src_original.parent.mkdir(parents=True, exist_ok=True)
                if backed_copy.is_dir():
                    if src_original.exists():
                        shutil.rmtree(src_original)
                    shutil.copytree(backed_copy, src_original)
                else:
                    shutil.copy2(backed_copy, src_original)
                restored.append(str(src_original))
            except Exception as exc:
                errors.append(f"Failed to restore {src_str}: {exc}")

        return {
            "success": len(errors) == 0,
            "backup_id": manifest["backup_id"],
            "backup_created_at": manifest.get("created_at"),
            "restored_files": restored,
            "errors": errors,
            "dry_run": dry_run,
        }

    def prune_old_backups(self) -> Dict[str, Any]:
        """
        Delete backups older than retention_days.

        Returns:
            Dict with pruned backup IDs and any errors.
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=self.retention_days)
        pruned: List[str] = []
        errors: List[str] = []

        for manifest in self.list_backups():
            try:
                created = datetime.fromisoformat(manifest["created_at"])
                if created < cutoff:
                    shutil.rmtree(manifest["backup_path"])
                    pruned.append(manifest["backup_id"])
            except Exception as exc:
                errors.append(f"{manifest.get('backup_id')}: {exc}")

        return {"pruned": pruned, "errors": errors}

    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Verify integrity of a specific backup using stored checksums.

        Returns:
            Dict with per-file verification results.
        """
        manifest = self.get_backup(backup_id)
        if manifest is None:
            return {"success": False, "error": f"Backup not found: {backup_id}"}

        backup_path = Path(manifest["backup_path"])
        stored = manifest.get("checksums", {})
        results: List[Dict[str, Any]] = []

        for src_str, expected_hash in stored.items():
            backed_copy = backup_path / Path(src_str).name
            if not backed_copy.exists():
                results.append({"file": src_str, "ok": False, "reason": "missing"})
                continue
            actual = self._sha256(backed_copy)
            ok = actual == expected_hash
            results.append({
                "file": src_str,
                "ok": ok,
                "reason": "ok" if ok else f"hash mismatch ({actual[:8]}…)",
            })

        all_ok = all(r["ok"] for r in results)
        return {"success": all_ok, "backup_id": backup_id, "files": results}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256(path: Optional[Path]) -> str:
        """Compute SHA-256 of a file, or return empty string for dirs/None."""
        if path is None or not path.is_file():
            return ""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
