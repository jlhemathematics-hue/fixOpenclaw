#!/usr/bin/env python3
"""
Comprehensive backup/restore test suite for FixOpenclaw.

Covers:
- Creating backups programmatically
- list-backups CLI mode
- restore-backup --dry-run
- restore-backup (actual restore, verifies file content)
- --backup-id selection (specific and invalid IDs)
- Checksum verification
- Prune old backups
"""

import sys
import os
import json
import time
import shutil
import subprocess
import tempfile
from pathlib import Path

# Make sure we run from the project root
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from src.utils.backup_manager import BackupManager

PASS = "[PASS]"
FAIL = "[FAIL]"
SECTION = "=" * 60


def section(title: str):
    print(f"\n{SECTION}")
    print(f"  {title}")
    print(SECTION)


def run_cli(*args) -> tuple[int, str]:
    """Run `python main.py <args>` from project root and return (exit_code, output)."""
    cmd = [sys.executable, "main.py"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    combined = result.stdout + result.stderr
    return result.returncode, combined


def assert_equal(label, actual, expected):
    if actual == expected:
        print(f"  {PASS}  {label}")
    else:
        print(f"  {FAIL}  {label}")
        print(f"         expected: {expected!r}")
        print(f"         actual  : {actual!r}")


def assert_in(label, needle, haystack):
    if needle in haystack:
        print(f"  {PASS}  {label}")
    else:
        print(f"  {FAIL}  {label}")
        print(f"         Looking for: {needle!r}")
        print(f"         In         : {haystack!r}")


def assert_not_in(label, needle, haystack):
    if needle not in haystack:
        print(f"  {PASS}  {label}")
    else:
        print(f"  {FAIL}  {label}")
        print(f"         Did not expect: {needle!r}")
        print(f"         In            : {haystack!r}")


def assert_true(label, condition, extra=""):
    if condition:
        print(f"  {PASS}  {label}")
    else:
        print(f"  {FAIL}  {label}{(' - ' + extra) if extra else ''}")


# ------------------------------------------------------------------ #
# Setup: create a fresh backup directory scoped to this test run
# ------------------------------------------------------------------ #

TEST_BACKUP_DIR = ROOT / "backups_test_run"
# Always start with a clean slate for test isolation
if TEST_BACKUP_DIR.exists():
    shutil.rmtree(str(TEST_BACKUP_DIR))
TEST_BACKUP_DIR.mkdir(parents=True)

# Dummy source files (use /tmp so we don't pollute project)
TMP_DIR = Path(tempfile.mkdtemp(prefix="fixopenclaw_test_"))
DUMMY_CONFIG = TMP_DIR / "test_config.yaml"
DUMMY_SETTINGS = TMP_DIR / "test_settings.json"
DUMMY_EXTRA = TMP_DIR / "test_extra.txt"

DUMMY_CONFIG.write_text("# Original config\nkey: value_original\n")
DUMMY_SETTINGS.write_text('{"setting": "original_value"}\n')
DUMMY_EXTRA.write_text("extra original content\n")

print(f"\nTest files created in: {TMP_DIR}")
print(f"Backup dir: {TEST_BACKUP_DIR}")


# ------------------------------------------------------------------ #
# TEST 1: Programmatic backup creation
# ------------------------------------------------------------------ #
section("TEST 1: Programmatic backup creation")

mgr = BackupManager(backup_dir=str(TEST_BACKUP_DIR), retention_days=7)

result1 = mgr.create_backup(
    source_paths=[str(DUMMY_CONFIG), str(DUMMY_SETTINGS)],
    label="test_backup_alpha",
    metadata={"note": "first test backup"},
)
print(f"  Backup result: {json.dumps(result1, indent=4)}")

assert_true("create_backup returns success", result1["success"])
assert_equal("files_backed_up count", result1["files_backed_up"], 2)
assert_equal("errors list is empty", result1["errors"], [])
assert_true("backup_id set", bool(result1["backup_id"]))
assert_true("backup_path exists on disk", Path(result1["backup_path"]).is_dir())

# Small sleep so the timestamps differ for ordering tests
time.sleep(1)

# Create a second backup (only one file, different content)
DUMMY_CONFIG.write_text("# Modified config\nkey: value_modified\n")
result2 = mgr.create_backup(
    source_paths=[str(DUMMY_CONFIG), str(DUMMY_EXTRA)],
    label="test_backup_beta",
)
print(f"\n  Second backup ID: {result2['backup_id']}")
assert_true("second create_backup returns success", result2["success"])

time.sleep(1)

# Third backup - all three files
result3 = mgr.create_backup(
    source_paths=[str(DUMMY_CONFIG), str(DUMMY_SETTINGS), str(DUMMY_EXTRA)],
    label="test_backup_gamma",
)
print(f"  Third backup ID: {result3['backup_id']}")
assert_true("third create_backup returns success", result3["success"])

BACKUP_ID_1 = result1["backup_id"]  # oldest
BACKUP_ID_2 = result2["backup_id"]  # middle
BACKUP_ID_3 = result3["backup_id"]  # latest


# ------------------------------------------------------------------ #
# TEST 2: list_backups (programmatic)
# ------------------------------------------------------------------ #
section("TEST 2: list_backups (programmatic)")

backups = mgr.list_backups()
print(f"  Found {len(backups)} backups")
for b in backups:
    print(f"    - {b['backup_id']}  label={b.get('label')}  files={len(b.get('files_backed_up',[]))}")

assert_equal("exactly 3 backups", len(backups), 3)
# Newest first
assert_equal("first in list is latest (gamma)", backups[0]["backup_id"], BACKUP_ID_3)
assert_equal("last in list is oldest (alpha)", backups[-1]["backup_id"], BACKUP_ID_1)


# ------------------------------------------------------------------ #
# TEST 3: get_latest_backup
# ------------------------------------------------------------------ #
section("TEST 3: get_latest_backup")

latest = mgr.get_latest_backup()
assert_true("get_latest_backup returns something", latest is not None)
assert_equal("latest backup is gamma", latest["backup_id"], BACKUP_ID_3)
print(f"  Latest backup: {latest['backup_id']}")


# ------------------------------------------------------------------ #
# TEST 4: get_backup by ID
# ------------------------------------------------------------------ #
section("TEST 4: get_backup by specific ID")

found = mgr.get_backup(BACKUP_ID_1)
assert_true("get_backup finds existing backup", found is not None)
assert_equal("correct backup returned", found["backup_id"], BACKUP_ID_1)

not_found = mgr.get_backup("backup_19991231_999999_nonexistent")
assert_equal("get_backup returns None for missing ID", not_found, None)
print(f"  get_backup({BACKUP_ID_1!r}) => found")
print(f"  get_backup('nonexistent') => None")


# ------------------------------------------------------------------ #
# TEST 5: restore_backup dry_run (latest)
# ------------------------------------------------------------------ #
section("TEST 5: restore_backup dry_run (latest backup)")

# Corrupt the dummy files so we can tell if restore really ran
DUMMY_CONFIG.write_text("# CORRUPTED\n")
DUMMY_SETTINGS.write_text('{"setting": "CORRUPTED"}\n')
DUMMY_EXTRA.write_text("CORRUPTED\n")

dry_result = mgr.restore_backup(verify_checksums=True, dry_run=True)
print(f"  dry_run result: {json.dumps(dry_result, indent=4)}")

assert_true("dry_run restore success=True", dry_result["success"])
assert_true("dry_run flag set in result", dry_result.get("dry_run", False))
assert_true("restored_files list not empty", len(dry_result["restored_files"]) > 0)
assert_in("dry_run restored_files contain DRY-RUN prefix",
          "[DRY-RUN]", " ".join(dry_result["restored_files"]))

# Files should still be CORRUPTED — dry-run must not write anything
assert_equal("CORRUPTED config untouched after dry-run",
             DUMMY_CONFIG.read_text(), "# CORRUPTED\n")
assert_equal("CORRUPTED settings untouched after dry-run",
             DUMMY_SETTINGS.read_text(), '{"setting": "CORRUPTED"}\n')


# ------------------------------------------------------------------ #
# TEST 6: restore_backup actual (latest backup = gamma)
# ------------------------------------------------------------------ #
section("TEST 6: restore_backup actual (latest = gamma)")

restore_result = mgr.restore_backup(verify_checksums=True, dry_run=False)
print(f"  restore result: {json.dumps(restore_result, indent=4)}")

assert_true("actual restore success=True", restore_result["success"])
assert_equal("no errors", restore_result["errors"], [])
assert_true("restored_files not empty", len(restore_result["restored_files"]) > 0)

# gamma backed up the modified config ("value_modified")
restored_config = DUMMY_CONFIG.read_text()
assert_equal("config restored to gamma version",
             restored_config, "# Modified config\nkey: value_modified\n")

restored_extra = DUMMY_EXTRA.read_text()
assert_equal("extra file restored correctly", restored_extra, "extra original content\n")


# ------------------------------------------------------------------ #
# TEST 7: restore specific backup by ID (alpha = original)
# ------------------------------------------------------------------ #
section("TEST 7: restore_backup by specific backup_id (alpha = original)")

# alpha only had DUMMY_CONFIG + DUMMY_SETTINGS with the original values
restore_alpha = mgr.restore_backup(backup_id=BACKUP_ID_1, verify_checksums=True, dry_run=False)
print(f"  restore alpha result: {json.dumps(restore_alpha, indent=4)}")

assert_true("restore by ID success=True", restore_alpha["success"])
assert_equal("correct backup_id in result", restore_alpha["backup_id"], BACKUP_ID_1)

restored_config_alpha = DUMMY_CONFIG.read_text()
assert_equal("config restored to alpha (original) version",
             restored_config_alpha, "# Original config\nkey: value_original\n")

restored_settings_alpha = DUMMY_SETTINGS.read_text()
assert_equal("settings restored to alpha version",
             restored_settings_alpha, '{"setting": "original_value"}\n')


# ------------------------------------------------------------------ #
# TEST 8: restore invalid backup_id
# ------------------------------------------------------------------ #
section("TEST 8: restore_backup with invalid backup_id")

bad_result = mgr.restore_backup(backup_id="backup_totally_fake_id")
print(f"  bad restore result: {json.dumps(bad_result, indent=4)}")

assert_equal("invalid ID returns success=False", bad_result["success"], False)
assert_true("error message mentions backup not found",
            "not found" in bad_result.get("error", "").lower()
            or "backup not found" in str(bad_result).lower())


# ------------------------------------------------------------------ #
# TEST 9: checksum verification catches tampering
# ------------------------------------------------------------------ #
section("TEST 9: Checksum verification catches tampered backup file")

# Tamper with the backup copy of DUMMY_CONFIG inside BACKUP_ID_2
backup2_path = Path(mgr.backup_dir) / BACKUP_ID_2
backed_config_copy = backup2_path / DUMMY_CONFIG.name
original_content = backed_config_copy.read_text()
backed_config_copy.write_text("TAMPERED CONTENT\n")

tamper_result = mgr.restore_backup(backup_id=BACKUP_ID_2, verify_checksums=True, dry_run=False)
print(f"  tampered restore result: {json.dumps(tamper_result, indent=4)}")

assert_equal("tampered restore success=False", tamper_result["success"], False)
assert_true("errors mention checksum mismatch",
            any("mismatch" in e.lower() or "checksum" in e.lower() for e in tamper_result["errors"]))

# Restore the tampered file for later tests
backed_config_copy.write_text(original_content)


# ------------------------------------------------------------------ #
# TEST 10: verify_backup
# ------------------------------------------------------------------ #
section("TEST 10: verify_backup integrity check")

vresult = mgr.verify_backup(BACKUP_ID_1)
print(f"  verify alpha: {json.dumps(vresult, indent=4)}")
assert_true("verify_backup success=True for untampered backup", vresult["success"])

# Non-existent backup
vbad = mgr.verify_backup("backup_does_not_exist")
assert_equal("verify_backup returns failure for missing backup", vbad["success"], False)


# ------------------------------------------------------------------ #
# TEST 11: create_backup with non-existent source file
# ------------------------------------------------------------------ #
section("TEST 11: create_backup with missing source file")

missing_result = mgr.create_backup(
    source_paths=["/tmp/this_file_definitely_does_not_exist_12345.yaml"],
)
print(f"  missing source result: {json.dumps(missing_result, indent=4)}")

assert_equal("missing source returns success=False", missing_result["success"], False)
assert_true("errors mention source not found",
            any("not found" in e.lower() for e in missing_result["errors"]))


# ------------------------------------------------------------------ #
# TEST 12: prune_old_backups (no-op since all are fresh)
# ------------------------------------------------------------------ #
section("TEST 12: prune_old_backups (no-op on fresh backups)")

prune = mgr.prune_old_backups()
print(f"  prune result: {prune}")
assert_equal("no fresh backups pruned", prune["pruned"], [])
assert_equal("no prune errors", prune["errors"], [])


# ------------------------------------------------------------------ #
# CLI TEST 13: list-backups via CLI (using default 'backups' dir)
# CLI tests use the real backups dir, so we create real backups first.
# ------------------------------------------------------------------ #
section("TEST 13: CLI list-backups (real backups dir)")

# Use the real backup dir for CLI tests
real_mgr = BackupManager(backup_dir=str(ROOT / "backups"), retention_days=7)

cli_file = TMP_DIR / "cli_test_file.txt"
cli_file.write_text("CLI test original content\n")

cli_backup = real_mgr.create_backup(
    source_paths=[str(cli_file)],
    label="cli_test",
)
print(f"  CLI backup created: {cli_backup['backup_id']}")
assert_true("CLI backup created successfully", cli_backup["success"])

exit_code, output = run_cli("--mode", "list-backups")
print(f"  CLI output:\n{output}")

assert_equal("list-backups exit code 0", exit_code, 0)
assert_in("output mentions cli_test backup", cli_backup["backup_id"], output)
assert_in("output shows total count", "Total:", output)
assert_in("latest marker shown", "← latest", output)
assert_not_in("output does not say 'No backups found'", "No backups found", output)


# ------------------------------------------------------------------ #
# CLI TEST 14: restore-backup --dry-run via CLI
# ------------------------------------------------------------------ #
section("TEST 14: CLI restore-backup --dry-run")

# Corrupt the file so we can check it's untouched
cli_file.write_text("CORRUPTED BY TEST 14\n")

exit_code, output = run_cli("--mode", "restore-backup", "--dry-run")
print(f"  CLI dry-run output:\n{output}")

assert_equal("dry-run exit code 0", exit_code, 0)
assert_in("output contains DRY-RUN mode warning", "DRY-RUN mode", output)
assert_in("output contains Restore successful", "Restore successful", output)

# File must still be corrupted
assert_equal("file untouched after CLI dry-run",
             cli_file.read_text(), "CORRUPTED BY TEST 14\n")


# ------------------------------------------------------------------ #
# CLI TEST 15: restore-backup actual via CLI
# ------------------------------------------------------------------ #
section("TEST 15: CLI restore-backup (actual)")

exit_code, output = run_cli("--mode", "restore-backup")
print(f"  CLI restore output:\n{output}")

assert_equal("restore exit code 0", exit_code, 0)
assert_in("output contains Restore successful", "Restore successful", output)

restored_content = cli_file.read_text()
assert_equal("file content restored via CLI",
             restored_content, "CLI test original content\n")


# ------------------------------------------------------------------ #
# CLI TEST 16: restore-backup with valid --backup-id
# ------------------------------------------------------------------ #
section("TEST 16: CLI restore-backup with valid --backup-id")

exit_code, output = run_cli("--mode", "restore-backup", "--backup-id", cli_backup["backup_id"])
print(f"  CLI restore by ID output:\n{output}")

assert_equal("restore by ID exit code 0", exit_code, 0)
assert_in("output contains Restore successful", "Restore successful", output)
assert_in("output shows the backup ID", cli_backup["backup_id"], output)


# ------------------------------------------------------------------ #
# CLI TEST 17: restore-backup with invalid --backup-id
# ------------------------------------------------------------------ #
section("TEST 17: CLI restore-backup with invalid --backup-id")

exit_code, output = run_cli("--mode", "restore-backup", "--backup-id", "backup_fake_id_xyz")
print(f"  CLI invalid ID output:\n{output}")

assert_equal("invalid backup ID returns exit code 1", exit_code, 1)
assert_in("output contains Backup not found", "Backup not found", output)


# ------------------------------------------------------------------ #
# CLI TEST 18: Interactive mode choice 5 (list backups)
# ------------------------------------------------------------------ #
section("TEST 18: Interactive mode - choice 5 (list backups)")

# Pipe input: choose 5 (list backups), then 7 (exit)
interactive_input = "5\n7\n"
cmd = [sys.executable, "main.py", "--mode", "interactive"]
proc = subprocess.run(
    cmd,
    input=interactive_input,
    capture_output=True,
    text=True,
    cwd=str(ROOT),
    timeout=30,
)
output = proc.stdout + proc.stderr
print(f"  Interactive list output:\n{output}")

assert_equal("interactive choice 5 exit code 0", proc.returncode, 0)
assert_in("output shows Available Backups header", "Available Backups", output)
assert_in("output includes cli backup ID", cli_backup["backup_id"], output)


# ------------------------------------------------------------------ #
# CLI TEST 19: Interactive mode choice 6 (restore latest backup)
# ------------------------------------------------------------------ #
section("TEST 19: Interactive mode - choice 6 (restore latest backup)")

# Corrupt the file again
cli_file.write_text("CORRUPTED FOR INTERACTIVE TEST\n")

# Pipe input: choice 6, blank backup_id (latest), dry-run=n, then exit
interactive_input = "6\n\nn\n7\n"
cmd = [sys.executable, "main.py", "--mode", "interactive"]
proc = subprocess.run(
    cmd,
    input=interactive_input,
    capture_output=True,
    text=True,
    cwd=str(ROOT),
    timeout=30,
)
output = proc.stdout + proc.stderr
print(f"  Interactive restore output:\n{output}")

assert_equal("interactive choice 6 exit code 0", proc.returncode, 0)
assert_in("output contains Restore successful", "Restore successful", output)

restored_content = cli_file.read_text()
assert_equal("file restored via interactive mode",
             restored_content, "CLI test original content\n")


# ------------------------------------------------------------------ #
# CLI TEST 20: Interactive mode choice 6 with dry-run=y
# ------------------------------------------------------------------ #
section("TEST 20: Interactive mode - choice 6 dry-run (y)")

cli_file.write_text("CORRUPTED FOR DRY-RUN INTERACTIVE\n")

# Pipe input: choice 6, blank backup_id (latest), dry-run=y, then exit
interactive_input = "6\n\ny\n7\n"
cmd = [sys.executable, "main.py", "--mode", "interactive"]
proc = subprocess.run(
    cmd,
    input=interactive_input,
    capture_output=True,
    text=True,
    cwd=str(ROOT),
    timeout=30,
)
output = proc.stdout + proc.stderr
print(f"  Interactive dry-run output:\n{output}")

assert_equal("interactive dry-run exit code 0", proc.returncode, 0)
assert_in("output contains DRY-RUN", "DRY-RUN", output)
assert_in("output contains Restore successful", "Restore successful", output)
assert_equal("file untouched after interactive dry-run",
             cli_file.read_text(), "CORRUPTED FOR DRY-RUN INTERACTIVE\n")


# ------------------------------------------------------------------ #
# Cleanup
# ------------------------------------------------------------------ #
section("Cleanup")
shutil.rmtree(str(TEST_BACKUP_DIR), ignore_errors=True)
shutil.rmtree(str(TMP_DIR), ignore_errors=True)
# Clean up real backup dir entries created by CLI tests
for b_id in [cli_backup["backup_id"]]:
    b_path = ROOT / "backups" / b_id
    if b_path.exists():
        shutil.rmtree(str(b_path))
print("  Test artifacts removed.")

print(f"\n{SECTION}")
print("  ALL TESTS COMPLETE")
print(SECTION + "\n")
