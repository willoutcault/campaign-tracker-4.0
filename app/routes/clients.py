from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Client, Pharma, Brand

clients_bp = Blueprint("clients", __name__)

def _sync_pharma_and_brands_for_client(name: str, brands_csv: str):
    # Ensure a Pharma exists with the client's name
    pharma = Pharma.query.filter_by(name=name).first()
    if not pharma:
        pharma = Pharma(name=name)
        db.session.add(pharma)
        db.session.flush()
    # Add any new brands under this Pharma
    brand_names = [b.strip() for b in (brands_csv or '').split(',') if b.strip()]
    for bn in brand_names:
        existing = Brand.query.filter_by(name=bn, pharma=pharma).first()
        if not existing:
            db.session.add(Brand(name=bn, pharma=pharma))

@clients_bp.route("/")
def list_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template("clients/list.html", clients=clients)

@clients_bp.route("/create", methods=["GET","POST"])
def create_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip() or None
        notes = request.form.get("notes", "").strip()
        default_brands = request.form.get("default_brands", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            db.session.add(Client(name=name, notes=notes))
            # Auto-create Pharma/Brands template for this client
            _sync_pharma_and_brands_for_client(name, default_brands)
            db.session.commit()
            flash("Client created (and Pharma/Brands synced).", "success")
            return redirect(url_for("clients.list_clients"))
    return render_template("clients/form.html", client=None)

@clients_bp.route("/<int:client_id>/edit", methods=["GET","POST"])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip() or None
        notes = request.form.get("notes", "").strip()
        default_brands = request.form.get("default_brands", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            # If the name changed, we still treat the current client name as Pharma name
            client.name = name
            client.notes = notes
            # Sync Pharma + Brands
            _sync_pharma_and_brands_for_client(name, default_brands)
            db.session.commit()
            flash("Client updated (and Pharma/Brands synced).", "success")
            return redirect(url_for("clients.list_clients"))
    return render_template("clients/form.html", client=client)
