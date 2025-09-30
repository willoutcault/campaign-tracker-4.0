import os
from dotenv import load_dotenv

def _sqlite_uri_for_instance(app):
    db_path = os.path.join(app.instance_path, "app.db").replace('\\', '/')
    return f"sqlite:///{db_path}"

def load_config(app):
    load_dotenv()
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    env_uri = os.getenv("DATABASE_URL")
    if not env_uri or env_uri.strip() == "":
        app.config["SQLALCHEMY_DATABASE_URI"] = _sqlite_uri_for_instance(app)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = env_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
    app.config["S3_BUCKET_NAME"] = os.getenv("S3_BUCKET_NAME", "")
    app.config["S3_PREFIX"] = os.getenv("S3_PREFIX", "target-lists/")
    app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024