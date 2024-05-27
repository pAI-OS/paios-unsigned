import connexion
from pathlib import Path
from flask import Blueprint
from flask_cors import CORS

def create_backend_app():
    # Conditional import based on the running context (module or script)
    try:
        from .auth import validate_bearer_token
    except ImportError:
        from auth import validate_bearer_token

    specification_dir = Path(__file__).resolve().parent.parent / 'apis' / 'paios'
    connexion_app = connexion.App(__name__, specification_dir=specification_dir)
    connexion_app.add_api('openapi.yaml')

    connexion_app.app.before_request(validate_bearer_token)

    return connexion_app

def create_and_register_backend(app, url_prefix='/api'):
    """
    Creates the backend blueprint, registers it with the provided Flask app,
    and configures CORS for the routes handled by this blueprint.

    Args:
        app (Flask): The main Flask application instance.
    """
    backend_bp = Blueprint('backend', __name__)
    connexion_app = create_backend_app()
    
    # Add the Connexion app's Flask app to the blueprint
    backend_bp.add_url_rule('/', 'backend', lambda: connexion_app.app)

    # Register the blueprint
    app.register_blueprint(backend_bp, url_prefix=url_prefix)

    # Configure CORS specifically for this blueprint
    CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=['X-Total-Count'], supports_credentials=True)

    return backend_bp
