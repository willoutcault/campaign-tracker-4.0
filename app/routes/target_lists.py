from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..extensions import db
from ..models import TargetList
from ..s3_utils import upload_fileobj

target_lists_bp = Blueprint("target_lists", __name__)

@target_lists_bp.route("/")
def list_target_lists():
    tls = TargetList.query.order_by(TargetList.uploaded_at.desc()).all()
    return render_template("target_lists/list.html", tls=tls)

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
