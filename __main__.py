import asyncio
import sys
import uvicorn
from pathlib import Path
from starlette.staticfiles import StaticFiles

# Ensure the parent directory is in sys.path so relative imports work.
base_dir = Path(__file__).parent
if base_dir not in sys.path:
    sys.path.append(str(base_dir))

def create_app():
    from backend.__main__ import create_backend_app
    app = create_backend_app()

    # Add a route for serving static files
    static_dir = Path(__file__).parent / 'frontend' / 'dist'
    app.add_url_rule(
        '/{path:path}', 
        endpoint='frontend', 
        view_func=StaticFiles(directory=static_dir, html=True)
    )

    return app

async def main():
    from backend.browser import await_open_browser

    host = 'localhost'
    port = 3080

    # Start the server and the wait_for_server_and_open_browser coroutine concurrently
    server = asyncio.create_task(asyncio.to_thread(uvicorn.run, "__main__:create_app", host=host, port=port, factory=True, workers=1))
    browser = asyncio.create_task(await_open_browser(host, port))

    await asyncio.gather(server, browser)

if __name__ == "__main__":
    asyncio.run(main())
