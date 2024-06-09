import sys
import signal
import asyncio
from pathlib import Path

# Ensure the parent directory is in sys.path so relative imports work.
base_dir = Path(__file__).parent
if base_dir not in sys.path:
    sys.path.append(str(base_dir))
from backend.env import check_env
from backend.paths import backend_dir, venv_dir

shutdown_event = asyncio.Event()

def handle_shutdown():
    print("Received exit signal...")
    shutdown_event.set()

async def main():
    # Check if the environment is set up and activated before importing dependencies
    check_env()
    from starlette.staticfiles import StaticFiles

    # Create the app
    from app import create_app
    app = create_app()

    # Run the app
    import uvicorn

    # Use ProactorEventLoop on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda s, f: handle_shutdown())

    config = uvicorn.Config(
        "app:create_app",
        host="localhost",
        port=3080,
        factory=True,
        workers=1,
        reload=True,
        reload_dirs=[backend_dir],
        reload_excludes=[venv_dir]
    )
    server = uvicorn.Server(config)

    server_task = asyncio.create_task(server.serve())
    await shutdown_event.wait()
    server.should_exit = True
    await server_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down...")
