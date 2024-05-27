import connexion
from pathlib import Path
from flask import Blueprint
from flask_cors import CORS

def create_backend_app():
    from auth import validate_bearer_token

    # Uses the connexion library to create a Flask app implmenting the OpenAPI
    # specification (../apis/paios/openapi.yaml), calling the python functions
    # in operationId (eg api.get_asset_by_id in api.py)

    specification_dir = Path(__file__).resolve().parent.parent / 'apis' / 'paios'
    connexion_app = connexion.App(__name__, specification_dir=specification_dir)
    CORS(connexion_app.app, expose_headers='X-Total-Count', supports_credentials=True)

    connexion_app.app.before_request(validate_bearer_token)

    connexion_app.add_api('openapi.yaml')

    return connexion_app

def create_backend_blueprint():
    backend_bp = Blueprint('backend', __name__)
    connexion_app = create_backend_app()
    
    # Add the Connexion app's Flask app to the blueprint
    backend_bp.add_url_rule('/', 'backend', lambda: connexion_app.app)

    return backend_bp
