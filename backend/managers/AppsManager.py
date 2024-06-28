from common.paths import apps_dir, venv_subdir, default_app_dir
from threading import Lock
import json

class AppsManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AppsManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self.default_env_dir = default_app_dir / venv_subdir
                    apps_dir.mkdir(parents=True, exist_ok=True)  # Create apps_dir if it doesn't exist
                    self.ensure_default_environment()
                    self._initialized = True

    def _create_venv(self, app_dir):
        import subprocess
        import sys

        """Create a virtual environment at the specified path."""
        venv_path = app_dir / '.venv'
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)

    def create_app(self, app_name='default', description='', version="0.1.0"):
        app_dir = apps_dir / app_name
        metadata_file = app_dir / 'metadata.json'

        if not app_dir.exists():
            app_dir.mkdir(parents=True, exist_ok=True)
        else:
            raise FileExistsError(f"App directory already exists at {app_dir}")

        if not metadata_file.exists():
            metadata = {
                "name": app_name,
                "description": description,
                "version": version
            }
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=4)
        else:
            raise FileExistsError(f"Metadata file already exists at {metadata_file}")

        # Create the virtual environment
        self._create_venv(app_dir)

# Example usage
if __name__ == "__main__":
    manager = AppsManager()
    manager.create_app("my-app", "This is a sample app")
