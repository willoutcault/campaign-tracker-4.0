
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from flask import current_app

def s3_client():
    return boto3.client("s3", region_name=current_app.config["AWS_REGION"])

def upload_fileobj(file_storage, key_prefix=None):
    bucket = current_app.config["S3_BUCKET_NAME"]
    prefix = key_prefix or current_app.config.get("S3_PREFIX", "target-lists/")
    ext = (file_storage.filename.rsplit(".", 1)[-1] if "." in file_storage.filename else "dat")
    key = f"{prefix}{uuid.uuid4().hex}.{ext}"
    client = s3_client()
    try:
        client.upload_fileobj(file_storage.stream, bucket, key, ExtraArgs={"ServerSideEncryption": "AES256"})
        return key
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")

def generate_presigned_get_url(key: str, expires_in: int = 300) -> str:
    """Return a temporary signed URL to download an object."""
    bucket = current_app.config["S3_BUCKET_NAME"]
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME not configured")
    client = s3_client()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in
        )
    except ClientError as e:
        raise RuntimeError(f"Presign failed: {e}")
