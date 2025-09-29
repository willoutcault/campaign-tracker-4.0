from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Pharma, Brand, Contract, Campaign, Program, Placement, TargetList

contracts_bp = Blueprint("contracts", __name__)
campaigns_bp = Blueprint("campaigns", __name__)
programs_bp = Blueprint("programs", __name__)
placements_bp = Blueprint("placements", __name__)

# -------- Contracts --------
@contracts_bp.route("/")
def list_contracts():
    contracts = Contract.query.order_by(Contract.id.desc()).all()
    return render_template("contracts/list.html", contracts=contracts)

@contracts_bp.route("/create", methods=["GET","POST"])
def create_contract():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pharma_name = request.form.get("pharma", "").strip()
        brand_names = [b.strip() for b in request.form.get("brands","").split(",") if b.strip()]
        if not name or not pharma_name:
            flash("Contract name and Pharma are required.", "danger")
            return render_template("contracts/form.html", contract=None)

        pharma = Pharma.query.filter_by(name=pharma_name).first()
        if not pharma:
            pharma = Pharma(name=pharma_name)
            db.session.add(pharma)
            db.session.flush()

        contract = Contract(name=name, pharma=pharma)
        db.session.add(contract)
        db.session.flush()

        # attach brands
        for bn in brand_names:
            b = Brand.query.filter_by(name=bn, pharma=pharma).first()
            if not b:
                b = Brand(name=bn, pharma=pharma)
                db.session.add(b)
                db.session.flush()
            contract.brands.append(b)

        db.session.commit()
        flash("Contract created.", "success")
        return redirect(url_for("contracts.list_contracts"))
    return render_template("contracts/form.html", contract=None)

@contracts_bp.route("/<int:contract_id>/edit", methods=["GET","POST"])
def edit_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pharma_name = request.form.get("pharma", "").strip()
        brand_names = [b.strip() for b in request.form.get("brands","").split(",") if b.strip()]
        if not name or not pharma_name:
            flash("Contract name and Pharma are required.", "danger")
        else:
            contract.name = name
            # pharma
            pharma = Pharma.query.filter_by(name=pharma_name).first()
            if not pharma:
                pharma = Pharma(name=pharma_name)
                db.session.add(pharma)
                db.session.flush()
            contract.pharma = pharma
            # brands
            contract.brands.clear()
            for bn in brand_names:
                b = Brand.query.filter_by(name=bn, pharma=pharma).first()
                if not b:
                    b = Brand(name=bn, pharma=pharma)
                    db.session.add(b)
                    db.session.flush()
                contract.brands.append(b)
            db.session.commit()
            flash("Contract updated.", "success")
            return redirect(url_for("contracts.list_contracts"))
    brands_csv = ", ".join([b.name for b in contract.brands])
    return render_template("contracts/form.html", contract=contract, brands_csv=brands_csv)

# -------- Campaigns --------
@campaigns_bp.route("/")
def list_campaigns():
    rows = Campaign.query.order_by(Campaign.id.desc()).all()
    return render_template("campaigns/list.html", campaigns=rows)

@campaigns_bp.route("/create", methods=["GET","POST"])
def create_campaign():
    from ..models import Contract
    contracts = Contract.query.order_by(Contract.name).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        contract_id = request.form.get("contract_id", type=int)
        desc = request.form.get("description","").strip()
        if not name or not contract_id:
            from flask import flash
            flash("Name and Contract are required.", "danger")
        else:
            c = Campaign(name=name, contract_id=contract_id, description=desc)
            db.session.add(c)
            db.session.commit()
            return redirect(url_for("campaigns.list_campaigns"))
    return render_template("campaigns/form.html", contracts=contracts, campaign=None)

@campaigns_bp.route("/<int:campaign_id>/edit", methods=["GET","POST"])
def edit_campaign(campaign_id):
    c = Campaign.query.get_or_404(campaign_id)
    from ..models import Contract
    contracts = Contract.query.order_by(Contract.name).all()
    if request.method == "POST":
        c.name = request.form.get("name","").strip()
        c.contract_id = request.form.get("contract_id", type=int)
        c.description = request.form.get("description","").strip()
        db.session.commit()
        return redirect(url_for("campaigns.list_campaigns"))
    return render_template("campaigns/form.html", contracts=contracts, campaign=c)

# -------- Programs --------
@programs_bp.route("/")
def list_programs():
    rows = Program.query.order_by(Program.id.desc()).all()
    return render_template("programs/list.html", programs=rows)

@programs_bp.route("/create", methods=["GET","POST"])
def create_program():
    campaigns = Campaign.query.order_by(Campaign.name).all()
    tls = TargetList.query.order_by(TargetList.uploaded_at.desc()).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        campaign_id = request.form.get("campaign_id", type=int)
        target_list_id = request.form.get("target_list_id", type=int)
        if not name or not campaign_id:
            from flask import flash
            flash("Name and Campaign are required.", "danger")
        else:
            prg = Program(name=name, campaign_id=campaign_id, target_list_id=target_list_id)
            db.session.add(prg)
            db.session.commit()
            return redirect(url_for("programs.list_programs"))
    return render_template("programs/form.html", programs=None, campaigns=campaigns, target_lists=tls)

@programs_bp.route("/<int:program_id>/edit", methods=["GET","POST"])
def edit_program(program_id):
    prg = Program.query.get_or_404(program_id)
    campaigns = Campaign.query.order_by(Campaign.name).all()
    tls = TargetList.query.order_by(TargetList.uploaded_at.desc()).all()
    if request.method == "POST":
        prg.name = request.form.get("name","").strip()
        prg.campaign_id = request.form.get("campaign_id", type=int)
        prg.target_list_id = request.form.get("target_list_id", type=int)
        db.session.commit()
        return redirect(url_for("programs.list_programs"))
    return render_template("programs/form.html", program=prg, campaigns=campaigns, target_lists=tls)

# -------- Placements --------
@placements_bp.route("/")
def list_placements():
    rows = Placement.query.order_by(Placement.id.desc()).all()
    return render_template("placements/list.html", placements=rows)

@placements_bp.route("/create", methods=["GET","POST"])
def create_placement():
    programs = Program.query.order_by(Program.name).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        program_id = request.form.get("program_id", type=int)
        channel = request.form.get("channel","").strip() or None
        status = request.form.get("status","").strip() or None
        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None
        if not name or not program_id:
            from flask import flash
            flash("Name and Program are required.", "danger")
        else:
            from datetime import date
            def parse_d(s):
                try:
                    return date.fromisoformat(s) if s else None
                except Exception:
                    return None
            pl = Placement(
                name=name, program_id=program_id, channel=channel, status=status,
                start_date=parse_d(start_date), end_date=parse_d(end_date)
            )
            db.session.add(pl)
            db.session.commit()
            return redirect(url_for("placements.list_placements"))
    return render_template("placements/form.html", programs=programs)
