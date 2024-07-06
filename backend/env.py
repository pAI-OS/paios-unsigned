# Check if the environment is set up correctly
def check_env():
    import os
    import sys
    from pathlib import Path

    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("Error: Running under the system python ({})\n".format(sys.prefix))
        venv_path = Path(__file__).resolve().parent.parent / '.venv'
        if not venv_path.exists():
            print("No virtual environment found at {} so you will need to create one.".format(venv_path))
            if os.name == "posix": # Linux/Mac
                print("\nYou can use the scripts/setup_environment.sh script to do this, or do it manually:",
                "    python3 -m venv .venv",
                "    source .venv/bin/activate",
                "    pip install -r backend/requirements.txt",
                sep="\n")
            elif os.name == "nt": # Windows
                print("\nYou can use the scripts\\setup_environment.ps1 script to do this, or do it manually from the root directory:\n",
                "    python -m venv .venv",
                "    .venv\\Scripts\\activate",
                "    pip install -r backend\\requirements.txt\n",
                sep="\n")
            sys.exit(1)
        else:
            print(f"Virtual environment found at {venv_path}. You can activate it with:\n")
            if os.name == "posix": # Linux/Mac
                print(f"    source {venv_path}/bin/activate")
            elif os.name == "nt": # Windows
                print(f"    {venv_path}\\Scripts\\activate.ps1")
            print(f"\nOnce you have activated the virtual environment, run this again.")
            sys.exit(1)

    required_modules = ['connexion', 'uvicorn']
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"Required module {module} is not installed.")
            sys.exit(1)
