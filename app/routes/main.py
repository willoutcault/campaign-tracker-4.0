from flask import Blueprint, render_template, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    sections = [
        ("Clients", "clients.list_clients"),
        ("Target Lists", "target_lists.list_target_lists"),
        ("Contracts", "contracts.list_contracts"),
        ("Campaigns", "campaigns.list_campaigns"),
        ("Programs", "programs.list_programs"),
        ("Placements", "placements.list_placements"),
    ]
    return render_template("index.html", sections=sections)
