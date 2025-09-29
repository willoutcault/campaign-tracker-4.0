import os
from dotenv import load_dotenv

def load_config(app):
    load_dotenv()
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # S3
    app.config["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
    app.config["S3_BUCKET_NAME"] = os.getenv("S3_BUCKET_NAME", "")
    app.config["S3_PREFIX"] = os.getenv("S3_PREFIX", "target-lists/")
    app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024  # 128 MB
