#!/usr/bin/env python3
"""
FixOpenclaw - Main Entry Point

Autonomous OpenClaw diagnostics and repair system.
"""

import sys
import time
import argparse
import signal
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.orchestrator import Orchestrator
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger
from src.utils.backup_manager import BackupManager


class FixOpenclawApp:
    """Main application class."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize application.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        log_config = self.config.get("logging", {})
        self.logger = setup_logger(
            name="fixopenclaw",
            level=log_config.get("level", "INFO"),
            log_file=log_config.get("file", "logs/fixopenclaw.log"),
            max_size=log_config.get("max_size", 10),
            backup_count=log_config.get("backup_count", 5),
            format_string=log_config.get("format")
        )

        # Initialize orchestrator
        self.orchestrator = Orchestrator(self.config)

        # Shutdown flag
        self.shutdown_requested = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info("Shutdown signal received")
        self.shutdown_requested = True

    def run_autonomous(self) -> None:
        """Run in autonomous mode."""
        self.logger.info("Starting FixOpenclaw in autonomous mode")

        # Start orchestrator
        self.orchestrator.start()

        # Get cycle interval
        cycle_interval = self.config.get("orchestrator", {}).get("cycle_interval", 60)

        try:
            while not self.shutdown_requested:
                # Run autonomous cycle
                self.logger.info("Running autonomous cycle")
                result = self.orchestrator.run_autonomous_cycle()

                # Log results
                if result["status"] == "success":
                    self.logger.info(
                        f"Cycle complete: {result.get('anomalies_detected', 0)} anomalies, "
                        f"{result.get('repairs_successful', 0)} repairs successful"
                    )
                else:
                    self.logger.error(f"Cycle failed: {result.get('message', 'Unknown error')}")

                # Sleep until next cycle
                if not self.shutdown_requested:
                    self.logger.info(f"Sleeping for {cycle_interval} seconds")
                    time.sleep(cycle_interval)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.orchestrator.stop()
            self.logger.info("FixOpenclaw stopped")

    def run_once(self, log_file: Optional[str] = None) -> None:
        """
        Run one-time diagnosis and repair.

        Args:
            log_file: Specific log file to analyze
        """
        self.logger.info("Running one-time diagnostic cycle")

        if log_file:
            self.logger.info(f"Analyzing log file: {log_file}")
            # Update config with specific log file
            if "monitoring" not in self.config:
                self.config["monitoring"] = {}
            self.config["monitoring"]["log_paths"] = [log_file]

        # Run single cycle
        result = self.orchestrator.run_autonomous_cycle()

        # Print results
        print("\n" + "=" * 60)
        print("FixOpenclaw Diagnostic Results")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Anomalies detected: {result.get('anomalies_detected', 0)}")
        print(f"Diagnostics completed: {result.get('diagnostics_completed', 0)}")
        print(f"Repairs attempted: {result.get('repairs_attempted', 0)}")
        print(f"Repairs successful: {result.get('repairs_successful', 0)}")
        print(f"Duration: {result.get('cycle_duration', 0):.2f} seconds")
        print("=" * 60 + "\n")

    def run_web_dashboard(self) -> None:
        """Run web dashboard."""
        self.logger.info("Starting web dashboard")

        try:
            import subprocess

            # Start orchestrator in background
            self.orchestrator.start()

            # Run Streamlit dashboard
            dashboard_config = self.config.get("dashboard", {})
            port = dashboard_config.get("port", 8501)

            self.logger.info(f"Starting Streamlit dashboard on port {port}")

            subprocess.run([
                "streamlit",
                "run",
                "ui/dashboard.py",
                "--server.port",
                str(port),
                "--server.headless",
                "true"
            ])

        except KeyboardInterrupt:
            self.logger.info("Dashboard shutdown requested")
        finally:
            self.orchestrator.stop()

    def run_restore_backup(
        self,
        backup_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Restore OpenClaw configuration from a backup.

        If backup_id is None, the most recent backup is used.

        Args:
            backup_id: Specific backup to restore (default: latest).
            dry_run: Simulate restore without writing any files.
        """
        backup_dir = self.config.get("system", {}).get("backup_dir", "backups")
        retention = self.config.get("system", {}).get("max_backup_age", 7)
        mgr = BackupManager(backup_dir=backup_dir, retention_days=retention)

        # Resolve the backup to use
        if backup_id:
            manifest = mgr.get_backup(backup_id)
            if manifest is None:
                print(f"\n❌  Backup not found: {backup_id}")
                sys.exit(1)
        else:
            manifest = mgr.get_latest_backup()
            if manifest is None:
                print("\n❌  No backups available.")
                sys.exit(1)

        print("\n" + "=" * 60)
        print("FixOpenclaw - Restore from Backup")
        print("=" * 60)
        print(f"Backup ID   : {manifest['backup_id']}")
        print(f"Created at  : {manifest.get('created_at', 'unknown')}")
        print(f"Label       : {manifest.get('label') or '—'}")
        print(f"Files       : {len(manifest.get('files_backed_up', []))}")
        if manifest.get("source_paths"):
            for p in manifest["source_paths"]:
                print(f"              • {p}")
        if dry_run:
            print("\n⚠️  DRY-RUN mode — no files will be changed")
        print("=" * 60)

        result = mgr.restore_backup(
            backup_id=manifest["backup_id"],
            verify_checksums=True,
            dry_run=dry_run,
        )

        print()
        if result["success"]:
            prefix = "[DRY-RUN] " if dry_run else ""
            print(f"✅  {prefix}Restore successful!")
            for f in result["restored_files"]:
                print(f"   ✓ {f}")
        else:
            print("❌  Restore failed:")
            for err in result["errors"]:
                print(f"   ✗ {err}")
            sys.exit(1)
        print("=" * 60 + "\n")

    def run_list_backups(self) -> None:
        """List all available backups."""
        backup_dir = self.config.get("system", {}).get("backup_dir", "backups")
        mgr = BackupManager(backup_dir=backup_dir)
        backups = mgr.list_backups()

        print("\n" + "=" * 60)
        print("FixOpenclaw - Available Backups")
        print("=" * 60)

        if not backups:
            print("  No backups found.")
        else:
            for i, b in enumerate(backups):
                marker = " ← latest" if i == 0 else ""
                print(f"\n  [{i + 1}] {b['backup_id']}{marker}")
                print(f"       Created : {b.get('created_at', '?')}")
                print(f"       Label   : {b.get('label') or '—'}")
                print(f"       Files   : {len(b.get('files_backed_up', []))}")
                if b.get("source_paths"):
                    for p in b["source_paths"]:
                        print(f"                 • {p}")

        print("\n" + "=" * 60)
        print(f"Total: {len(backups)} backup(s)")
        print("=" * 60 + "\n")

    def run_interactive(self) -> None:
        """Run in interactive mode."""
        self.logger.info("Starting interactive mode")

        print("\n" + "=" * 60)
        print("FixOpenclaw - Interactive Mode")
        print("=" * 60)

        # Start orchestrator
        self.orchestrator.start()

        try:
            while not self.shutdown_requested:
                print("\nCommands:")
                print("  1. Run monitoring")
                print("  2. View system status")
                print("  3. View metrics")
                print("  4. Run full cycle")
                print("  5. List backups")
                print("  6. Restore latest backup")
                print("  7. Exit")

                choice = input("\nEnter choice (1-7): ").strip()

                if choice == "1":
                    result = self.orchestrator.trigger_monitoring()
                    print(f"\nMonitoring complete: {len(result.get('anomalies', []))} anomalies detected")

                elif choice == "2":
                    status = self.orchestrator.get_system_status()
                    print("\nSystem Status:")
                    print(f"  Status: {status['system_state']['status']}")
                    print(f"  Anomalies detected: {status['system_state']['total_anomalies_detected']}")
                    print(f"  Repairs attempted: {status['system_state']['total_repairs_attempted']}")
                    print(f"  Repairs successful: {status['system_state']['total_repairs_successful']}")

                elif choice == "3":
                    metrics = self.orchestrator.get_metrics()
                    print("\nMetrics:")
                    for key, value in metrics.items():
                        print(f"  {key}: {value}")

                elif choice == "4":
                    print("\nRunning full cycle...")
                    result = self.orchestrator.run_autonomous_cycle()
                    print(f"Cycle complete: {result['status']}")

                elif choice == "5":
                    self.run_list_backups()

                elif choice == "6":
                    backup_id = input("  Backup ID (leave blank for latest): ").strip() or None
                    dry = input("  Dry run? (y/N): ").strip().lower() == "y"
                    self.run_restore_backup(backup_id=backup_id, dry_run=dry)

                elif choice == "7":
                    break

                else:
                    print("Invalid choice")

        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.orchestrator.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FixOpenclaw - Autonomous OpenClaw diagnostics and repair system"
    )

    parser.add_argument(
        "--mode",
        choices=["auto", "once", "web", "interactive", "restore-backup", "list-backups"],
        default="auto",
        help="Operation mode (default: auto)"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file to analyze (for 'once' mode)"
    )

    parser.add_argument(
        "--backup-id",
        type=str,
        default=None,
        help="Backup ID to restore (for 'restore-backup' mode; default: latest)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate restore without writing any files (for 'restore-backup' mode)"
    )

    args = parser.parse_args()

    # Create app
    try:
        app = FixOpenclawApp(config_path=args.config)

        # Run in selected mode
        if args.mode == "auto":
            app.run_autonomous()
        elif args.mode == "once":
            app.run_once(log_file=args.log_file)
        elif args.mode == "web":
            app.run_web_dashboard()
        elif args.mode == "interactive":
            app.run_interactive()
        elif args.mode == "restore-backup":
            app.run_restore_backup(backup_id=args.backup_id, dry_run=args.dry_run)
        elif args.mode == "list-backups":
            app.run_list_backups()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
