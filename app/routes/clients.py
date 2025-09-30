
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Client, Pharma, Brand
from ..helpers import get_page, get_per_page, apply_search

clients_bp = Blueprint("clients", __name__)

def _sync_pharma_and_brands_for_client(name: str, brands_csv: str):
    pharma = Pharma.query.filter_by(name=name).first()
    if not pharma:
        pharma = Pharma(name=name)
        db.session.add(pharma)
        db.session.flush()
    brand_names = [b.strip() for b in (brands_csv or '').split(',') if b.strip()]
    for bn in brand_names:
        existing = Brand.query.filter_by(name=bn, pharma=pharma).first()
        if not existing:
            db.session.add(Brand(name=bn, pharma=pharma))

@clients_bp.route("/")
def list_clients():
    page = get_page()
    per_page = get_per_page(15)
    query = Client.query.order_by(Client.created_at.desc())
    query, q = apply_search(query, Client, ["name", "notes"])
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("clients/list.html", clients=rows, total=total, page=page, per_page=per_page, q=q)

@clients_bp.route("/create", methods=["GET","POST"])
def create_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()
        default_brands = request.form.get("default_brands", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            db.session.add(Client(name=name, notes=notes))
            _sync_pharma_and_brands_for_client(name, default_brands)
            db.session.commit()
            flash("Client created (and Pharma/Brands synced).", "success")
            return redirect(url_for("clients.list_clients"))
    return render_template("clients/form.html", client=None, mapped_brands=[], pharma_name=None)

@clients_bp.route("/<int:client_id>/edit", methods=["GET","POST"])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()
        default_brands = request.form.get("default_brands", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            client.name = name
            client.notes = notes
            _sync_pharma_and_brands_for_client(name, default_brands)
            db.session.commit()
            flash("Client updated (and Pharma/Brands synced).", "success")
            return redirect(url_for("clients.edit_client", client_id=client.id))

    pharma = Pharma.query.filter_by(name=client.name).first()
    mapped_brands = pharma.brands if pharma else []
    return render_template("clients/form.html", client=client, mapped_brands=mapped_brands, pharma_name=(pharma.name if pharma else None))
