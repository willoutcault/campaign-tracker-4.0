from flask import Flask
from .config import load_config
from .extensions import db
from .routes.main import main_bp
from .routes.clients import clients_bp
from .routes.target_lists import target_lists_bp
from .routes.programs_targetlist_api import programs_bp
from .routes.placements_edit_override import placements_bp
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
    with app.app_context():
        db.create_all()
    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(target_lists_bp, url_prefix="/target-lists")
    app.register_blueprint(contracts_bp, url_prefix="/contracts")
    app.register_blueprint(campaigns_bp, url_prefix="/campaigns")
    app.register_blueprint(programs_bp, url_prefix="/programs")
    app.register_blueprint(placements_bp, url_prefix="/placements")
    # simple index redirect
    @app.route("/")
    def index():
        return '<div style="padding:16px"><a href="/contracts">Contracts</a></div>'
    return app