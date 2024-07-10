import sys
import signal
import asyncio
from pathlib import Path

# Ensure the parent directory is in sys.path so relative imports work.
base_dir = Path(__file__).parent
if base_dir not in sys.path:
    sys.path.append(str(base_dir))
from backend.env import check_env
from common.paths import base_dir, backend_dir, venv_subdir

def handle_keyboard_interrupt(signum, frame):
    print(f"KeyboardInterrupt (ID: {signum}) has been caught. Cleaning up...")
    cleanup()
    asyncio.get_event_loop().stop()

def cleanup():
    # Perform any necessary cleanup here
    print("Performing cleanup tasks...")

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_keyboard_interrupt)
    signal.signal(signal.SIGTERM, handle_keyboard_interrupt)

    # Check if the environment is set up and activated before importing dependencies
    check_env()
    from starlette.staticfiles import StaticFiles

    # Create the app
    from app import create_app
    app = create_app()

    # Run the app
    import uvicorn
    try:
        uvicorn.run("app:create_app", host="localhost", port=3080, factory=True, workers=1, reload=True, reload_dirs=[backend_dir], reload_excludes=[base_dir / venv_subdir])
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
