# app/routes/target_lists.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Pharma, Brand, TargetList
from flask import current_app as app

import io
import time

try:
    import boto3
except Exception:
    boto3 = None

target_lists_bp = Blueprint("target_lists", __name__)

def parse_int_list(values):
    out = []
    for v in values:
        try:
            out.append(int(v))
        except Exception:
            pass
    return out

def _require_s3_client():
    if not boto3:
        raise RuntimeError("boto3 not installed. `pip install boto3`")
    region = app.config.get("AWS_REGION") or "us-east-1"
    return boto3.client("s3", region_name=region)

def _upload_to_s3(file_storage, bucket, key, kms_key_id=None, acl=None):
    """
    Uploads the given Werkzeug file to S3 and returns (s3_key, original_filename, size_bytes).
    """
    filename = secure_filename(file_storage.filename or f"upload-{int(time.time())}")
    # Read into memory for reliable size
    data = file_storage.read()
    size_bytes = len(data)
    file_storage.stream.close()

    client = _require_s3_client()

    extra = {}
    # Optional server-side encryption
    if kms_key_id:
        extra["ServerSideEncryption"] = "aws:kms"
        extra["SSEKMSKeyId"] = kms_key_id
    elif app.config.get("S3_ENCRYPTION", "").lower() == "aes256":
        extra["ServerSideEncryption"] = "AES256"

    # Optional ACL
    if acl:
        extra["ACL"] = acl

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        **extra,
    )
    return key, filename, size_bytes

@target_lists_bp.route("/")
def list_target_lists():
    tls = TargetList.query.order_by(TargetList.uploaded_at.desc()).all()
    return render_template("target_lists/list.html", target_lists=tls)

@target_lists_bp.route("/create", methods=["GET","POST"])
def create_target_list():
    pharmas = Pharma.query.order_by(Pharma.name).all()
    brands = Brand.query.order_by(Brand.name).all()
    if request.method == "POST":
        label = (request.form.get("label") or "").strip()

        # Either a file OR an existing s3_key may be provided
        file_storage = request.files.get("file")
        pasted_s3_key = (request.form.get("s3_key") or "").strip()

        if not label:
            flash("Label is required.", "danger")
            return render_template("target_lists/form.html", tl=None, pharmas=pharmas, brands=brands,
                                   selected_pharma_ids=[], selected_brand_ids=[])

        s3_key = None
        original_filename = None
        size_bytes = None

        bucket = app.config.get("S3_BUCKET_NAME")
        prefix = app.config.get("S3_PREFIX", "target-lists/")
        kms_key_id = app.config.get("S3_KMS_KEY_ID")  # optional
        acl = app.config.get("S3_ACL")               # optional (e.g., "private")

        if file_storage and getattr(file_storage, "filename", ""):
            if not bucket:
                flash("S3 bucket is not configured. Set S3_BUCKET_NAME in your environment.", "danger")
                return render_template("target_lists/form.html", tl=None, pharmas=pharmas, brands=brands,
                                       selected_pharma_ids=[], selected_brand_ids=[])

            # Build an S3 key: <prefix><epoch>-<filename>
            safe = secure_filename(file_storage.filename)
            ts = int(time.time())
            key = f"{prefix}{ts}-{safe}"

            try:
                s3_key, original_filename, size_bytes = _upload_to_s3(
                    file_storage, bucket=bucket, key=key, kms_key_id=kms_key_id, acl=acl
                )
            except Exception as e:
                flash(f"Upload to S3 failed: {e}", "danger")
                return render_template("target_lists/form.html", tl=None, pharmas=pharmas, brands=brands,
                                       selected_pharma_ids=[], selected_brand_ids=[])
        elif pasted_s3_key:
            s3_key = pasted_s3_key
            original_filename = (request.form.get("original_filename") or "").strip() or s3_key.split("/")[-1]
            size_bytes = None
        else:
            flash("Please choose a file to upload OR paste an existing S3 key.", "danger")
            return render_template("target_lists/form.html", tl=None, pharmas=pharmas, brands=brands,
                                   selected_pharma_ids=[], selected_brand_ids=[])

        tl = TargetList(
            label=label,
            s3_key=s3_key,
            original_filename=original_filename or "",
            size_bytes=size_bytes
        )
        db.session.add(tl)
        db.session.flush()

        pharma_ids = parse_int_list(request.form.getlist("pharma_ids"))
        brand_ids = parse_int_list(request.form.getlist("brand_ids"))
        if pharma_ids:
            tl.pharmas = Pharma.query.filter(Pharma.id.in_(pharma_ids)).all()
        if brand_ids:
            tl.brands = Brand.query.filter(Brand.id.in_(brand_ids)).all()

        db.session.commit()
        flash("Target List created.", "success")
        return redirect(url_for("target_lists.list_target_lists"))

    return render_template("target_lists/form.html", tl=None, pharmas=pharmas, brands=brands,
                           selected_pharma_ids=[], selected_brand_ids=[])

@target_lists_bp.route("/<int:tl_id>/edit", methods=["GET","POST"])
def edit_target_list(tl_id):
    tl = TargetList.query.get_or_404(tl_id)
    pharmas = Pharma.query.order_by(Pharma.name).all()
    brands = Brand.query.order_by(Brand.name).all()

    if request.method == "POST":
        tl.label = (request.form.get("label") or tl.label).strip() or tl.label
        # Allow replacing file OR changing s3_key manually
        file_storage = request.files.get("file")
        pasted_s3_key = (request.form.get("s3_key") or "").strip()

        bucket = app.config.get("S3_BUCKET_NAME")
        prefix = app.config.get("S3_PREFIX", "target-lists/")
        kms_key_id = app.config.get("S3_KMS_KEY_ID")
        acl = app.config.get("S3_ACL")

        if file_storage and getattr(file_storage, "filename", ""):
            if not bucket:
                flash("S3 bucket is not configured. Set S3_BUCKET_NAME.", "danger")
                return render_template("target_lists/form.html", tl=tl, pharmas=pharmas, brands=brands,
                                       selected_pharma_ids={p.id for p in tl.pharmas},
                                       selected_brand_ids={b.id for b in tl.brands})
            safe = secure_filename(file_storage.filename)
            ts = int(time.time())
            key = f"{prefix}{ts}-{safe}"
            try:
                s3_key, original_filename, size_bytes = _upload_to_s3(
                    file_storage, bucket=bucket, key=key, kms_key_id=kms_key_id, acl=acl
                )
                tl.s3_key = s3_key
                tl.original_filename = original_filename
                tl.size_bytes = size_bytes
            except Exception as e:
                flash(f"Upload to S3 failed: {e}", "danger")
                return render_template("target_lists/form.html", tl=tl, pharmas=pharmas, brands=brands,
                                       selected_pharma_ids={p.id for p in tl.pharmas},
                                       selected_brand_ids={b.id for b in tl.brands})
        elif pasted_s3_key:
            tl.s3_key = pasted_s3_key
            tl.original_filename = (request.form.get("original_filename") or "").strip() or pasted_s3_key.split("/")[-1]

        # Update mappings
        pharma_ids = parse_int_list(request.form.getlist("pharma_ids"))
        brand_ids = parse_int_list(request.form.getlist("brand_ids"))
        tl.pharmas = Pharma.query.filter(Pharma.id.in_(pharma_ids)).all() if pharma_ids else []
        tl.brands = Brand.query.filter(Brand.id.in_(brand_ids)).all() if brand_ids else []

        db.session.commit()
        flash("Target List updated.", "success")
        return redirect(url_for("target_lists.list_target_lists"))

    selected_pharma_ids = {p.id for p in tl.pharmas}
    selected_brand_ids = {b.id for b in tl.brands}
    return render_template("target_lists/form.html", tl=tl, pharmas=pharmas, brands=brands,
                           selected_pharma_ids=selected_pharma_ids, selected_brand_ids=selected_brand_ids)
