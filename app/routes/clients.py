from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Client

clients_bp = Blueprint("clients", __name__)

@clients_bp.route("/")
def list_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template("clients/list.html", clients=clients)

@clients_bp.route("/create", methods=["GET","POST"])
def create_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            db.session.add(Client(name=name, notes=notes))
            db.session.commit()
            flash("Client created", "success")
            return redirect(url_for("clients.list_clients"))
    return render_template("clients/form.html", client=None)

@clients_bp.route("/<int:client_id>/edit", methods=["GET","POST"])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("Name is required", "danger")
        else:
            client.name = name
            client.notes = notes
            db.session.commit()
            flash("Client updated", "success")
            return redirect(url_for("clients.list_clients"))
    return render_template("clients/form.html", client=client)
