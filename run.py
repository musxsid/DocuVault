"""
DocuVaultAI — Unified Execution Launcher CLI
Provides unified commands to run Desktop GUI, Cloud Web Hub, Flask Backend,
generate sample test documents, or execute the Unit Test Suite.

Usage:
    python run.py --desktop       # Launch PyQt6 Native Desktop Application
    python run.py --web           # Launch Flask API + Streamlit Cloud Web Hub
    python run.py --backend       # Launch Flask REST API microservice (port 5000)
    python run.py --samples       # Generate realistic sample documents in vault/intake
    python run.py --test          # Run full Unit Test Suite (Units 1 to 5)
    python run.py --sort          # Run file sorter daemon on intake folder
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Fix Windows cp1252 console encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_desktop():
    print("[DocuVault] Launching PyQt6 Native Desktop GUI...")
    from ui.desktop_pyqt import main as desktop_main
    desktop_main()


def run_backend(port: int = 5000):
    print(f"[DocuVault] Starting Flask REST Service on port {port}...")
    from backend.app_flask import run_server
    run_server(port=port, debug=False)


def run_web():
    print("[DocuVault] Starting Flask Backend + Streamlit Cloud Web Hub...")
    # Spawn Flask in background
    flask_proc = subprocess.Popen([sys.executable, "run.py", "--backend"])
    try:
        # Run Streamlit in foreground
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "ui/dashboard_streamlit.py",
            "--server.port=8501", "--server.headless=false"
        ])
    finally:
        flask_proc.terminate()


def generate_samples():
    print("[DocuVault] Generating sample test documents...")
    from generate_samples import generate_all_samples
    generate_all_samples()


def run_tests():
    print("[DocuVault] Running Unit Test Suite (Units 1 to 5)...")
    import unittest
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


def run_sorter():
    print("[DocuVault] Running Automated File Sorter on vault/intake...")
    from core.organizer import FileOrganizerDaemon
    sorter = FileOrganizerDaemon(vault_root="vault")
    results = sorter.process_intake_folder()
    print(f"Processed {len(results)} files. See file_ops.log for operations audit trail.")


def main():
    parser = argparse.ArgumentParser(description="DocuVaultAI — Unified System Launcher")
    parser.add_argument("--desktop", action="store_true", help="Launch PyQt6 Native Desktop Application")
    parser.add_argument("--web", action="store_true", help="Launch Flask REST API and Streamlit Cloud Hub")
    parser.add_argument("--backend", action="store_true", help="Launch Flask REST API Server on port 5000")
    parser.add_argument("--samples", action="store_true", help="Generate sample documents in vault/intake")
    parser.add_argument("--test", action="store_true", help="Run comprehensive Unit Test Suite (Units 1-5)")
    parser.add_argument("--sort", action="store_true", help="Execute automated file sorter on intake folder")

    args = parser.parse_args()

    if args.desktop:
        run_desktop()
    elif args.web:
        run_web()
    elif args.backend:
        run_backend()
    elif args.samples:
        generate_samples()
    elif args.test:
        run_tests()
    elif args.sort:
        run_sorter()
    else:
        # Default action: launch desktop app
        print("No flag specified. Defaulting to Desktop GUI. (Use --help to view options)")
        run_desktop()


if __name__ == "__main__":
    main()
