#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil
import argparse
from pathlib import Path
from collections.abc import Sequence
from typing import Optional

# Ensure the parent directory is in sys.path so relative imports work.
base_dir = Path(__file__).parent.parent
if base_dir not in sys.path:
    sys.path.append(str(base_dir))

from common.paths import base_dir, venv_dir, backend_dir, frontend_dir, env_file

# Determine the correct path for the Python executable based on the OS
if os.name == 'nt':  # Windows
    venv_python = venv_dir / 'Scripts' / 'python'
else:  # POSIX (Linux, macOS, etc.)
    venv_python = venv_dir / 'bin' / 'python'

SUCCESS = 0

def setup_backend():
    print("Setting up the backend environment...")
    # Use the system Python to create the virtual environment
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    # Use the Python executable from the virtual environment to install dependencies
    subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(backend_dir / "requirements.txt")], check=True)

def build_frontend():
    print("Setting up the frontend environment...")
    npm_path = shutil.which("npm")
    if npm_path:
        current_dir = os.getcwd()
        os.chdir(frontend_dir)
        subprocess.run([npm_path, "install"], check=True)
        subprocess.run([npm_path, "run", "build"], check=True)
        os.chdir(current_dir)
    else:
        print("Skipped as npm command not found.")
        print("Download Node.js to build the frontend or use a prebuilt version (e.g. canary branch): https://nodejs.org/en/download")

def setup_vscode():
    print("Setting up VSCode configuration...")
    vscode_dir = base_dir / '.vscode'
    vscode_dir.mkdir(exist_ok=True)
    
    sample_files = list(vscode_dir.glob('*.sample'))
    for sample_file in sample_files:
        target_file = vscode_dir / sample_file.stem
        if not target_file.exists():
            shutil.copy(sample_file, target_file)
            print(f"Copied {sample_file} to {target_file}")

def main(argv: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(
        description="Setup you paios environment by installing the requisite dependencies."
    )
    parser.add_argument(
        "--vscode", 
        required=False, 
        action="store_true",
        help="Setup vscode configuration."
    )

    args = parser.parse_args(argv)

    setup_backend()
    build_frontend()

    if args.vscode:
        setup_vscode()

    print("Setup complete.")
    return SUCCESS

if __name__ == "__main__":
    SystemExit(main())
