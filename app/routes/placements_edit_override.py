
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..extensions import db
from ..models import Pharma, Brand, Contract, Campaign, Program, Placement, TargetList

contracts_bp = Blueprint("contracts", __name__)
campaigns_bp = Blueprint("campaigns", __name__)
programs_bp = Blueprint("programs", __name__)
placements_bp = Blueprint("placements", __name__)

def parse_date(s):
    from datetime import date
    try:
        return date.fromisoformat(s) if s else None
    except Exception:
        return None

@placements_bp.route("/<int:placement_id>/edit", methods=["GET","POST"])
def edit_placement(placement_id):
    pl = Placement.query.get_or_404(placement_id)
    programs = Program.query.order_by(Program.name).all()
    if request.method == "POST":
        pl.name = request.form.get("name","").strip()
        program_ids = request.form.getlist("program_ids", type=int)
        pl.channel = request.form.get("channel","").strip() or None
        pl.status = request.form.get("status","").strip() or None
        pl.start_date = parse_date(request.form.get("start_date"))
        pl.end_date = parse_date(request.form.get("end_date"))
        pl.placement_code = request.form.get("placement_code","").strip() or None
        pl.format = request.form.get("format","").strip() or None
        pl.frequency_cap = request.form.get("frequency_cap", type=int)
        pl.ad_server = request.form.get("ad_server","").strip() or None
        pl.impression_goal = request.form.get("impression_goal", type=int)
        pl.click_goal = request.form.get("click_goal", type=int)
        chosen = Program.query.filter(Program.id.in_(program_ids)).all() if program_ids else []
        pl.programs = chosen
        db.session.commit()
        flash("Placement updated.", "success")
        nxt = request.form.get("next")
        if nxt:
            return redirect(nxt)
        return redirect(url_for("placements.list_placements"))
    selected_program_ids = {p.id for p in pl.programs}
    return render_template("placements/form.html", programs=programs, placement=pl, selected_program_ids=selected_program_ids)
