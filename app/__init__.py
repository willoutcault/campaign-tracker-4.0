from flask import Flask
from .config import load_config
from .extensions import db
from .routes.main import main_bp
from .routes.clients import clients_bp
from .routes.target_lists import target_lists_bp
from .routes.campaigns_programs import contracts_bp, campaigns_bp, programs_bp, placements_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder="templates", static_folder="static")
    load_config(app)
    # Ensure instance folder exists
    try:
        import os
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    db.init_app(app)

    # Auto-create tables on startup if they don't exist
    with app.app_context():
        db.create_all()

    # register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(target_lists_bp, url_prefix="/target-lists")
    app.register_blueprint(contracts_bp, url_prefix="/contracts")
    app.register_blueprint(campaigns_bp, url_prefix="/campaigns")
    app.register_blueprint(programs_bp, url_prefix="/programs")
    app.register_blueprint(placements_bp, url_prefix="/placements")
    return app
