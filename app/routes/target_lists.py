
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from ..extensions import db
from ..models import TargetList
from ..s3_utils import upload_fileobj, generate_presigned_get_url
from ..helpers import get_page, get_per_page, apply_search

target_lists_bp = Blueprint("target_lists", __name__)

@target_lists_bp.route("/")
def list_target_lists():
    page = get_page()
    per_page = get_per_page(15)
    query = TargetList.query.order_by(TargetList.uploaded_at.desc())
    query, q = apply_search(query, TargetList, ["label", "original_filename", "s3_key"])
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("target_lists/list.html", tls=rows, total=total, page=page, per_page=per_page, q=q)

@target_lists_bp.route("/upload", methods=["GET", "POST"])
def upload_target_list():
    if request.method == "POST":
        file = request.files.get("file")
        label = request.form.get("label", "").strip() or (file.filename if file else "")
        if not file:
            flash("Please choose a file to upload.", "danger")
            return redirect(request.url)

        if not current_app.config.get("S3_BUCKET_NAME"):
            flash("S3_BUCKET_NAME is not configured. Check your .env.", "danger")
            return redirect(request.url)

        key = upload_fileobj(file)
        tl = TargetList(
            label=label or file.filename,
            s3_key=key,
            original_filename=file.filename,
            size_bytes=file.content_length or 0,
        )
        db.session.add(tl)
        db.session.commit()
        flash("Target List uploaded.", "success")
        return redirect(url_for("target_lists.list_target_lists"))
    return render_template("target_lists/upload.html")

@target_lists_bp.route("/<int:tl_id>/download")
def download_target_list(tl_id):
    tl = TargetList.query.get_or_404(tl_id)
    try:
        url = generate_presigned_get_url(tl.s3_key, expires_in=300)
        return redirect(url)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("target_lists.list_target_lists"))
