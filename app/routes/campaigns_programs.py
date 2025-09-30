
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..extensions import db
from ..models import Pharma, Brand, Contract, Campaign, Program, Placement, TargetList
from ..helpers import get_page, get_per_page, apply_search

contracts_bp = Blueprint("contracts", __name__)
campaigns_bp = Blueprint("campaigns", __name__)
programs_bp = Blueprint("programs", __name__)
placements_bp = Blueprint("placements", __name__)

# -------- Contracts (searchable list, view, create/edit, nested creates) --------
@contracts_bp.route("/")
def list_contracts():
    page = get_page()
    per_page = get_per_page(15)
    query = Contract.query.order_by(Contract.id.desc())
    q = (request.args.get("q") or "").strip()
    if q:
        query = query.join(Pharma).outerjoin(Contract.brands).filter(
            (Contract.name.ilike(f"%{q}%")) | (Pharma.name.ilike(f"%{q}%")) | (Brand.name.ilike(f"%{q}%"))
        )
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("contracts/list.html", contracts=rows, total=total, page=page, per_page=per_page, q=q)

@contracts_bp.route("/<int:contract_id>")
def view_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    campaigns = Campaign.query.filter_by(contract_id=contract.id).order_by(Campaign.name).all()
    programs_by_campaign = {}
    for c in campaigns:
        programs_by_campaign[c.id] = Program.query.filter_by(campaign_id=c.id).order_by(Program.name).all()
    all_programs = Program.query.join(Campaign, Program.campaign_id == Campaign.id).filter(Campaign.contract_id == contract.id).order_by(Program.name).all()
    return render_template("contracts/view.html",
                        contract=contract,
                        campaigns=campaigns,
                        programs_by_campaign=programs_by_campaign,
                        all_programs=all_programs)

@contracts_bp.route("/api/brands/<int:pharma_id>")
def api_brands(pharma_id):
    pharma = Pharma.query.get_or_404(pharma_id)
    data = [{"id": b.id, "name": b.name} for b in pharma.brands]
    return jsonify(data)

@contracts_bp.route("/create", methods=["GET","POST"])
def create_contract():
    pharmas = Pharma.query.order_by(Pharma.name).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pharma_id = request.form.get("pharma_id", type=int)
        brand_ids = request.form.getlist("brand_ids", type=int)
        pharma_name = request.form.get("pharma", "").strip()
        brands_csv = request.form.get("brands", "").strip()
        if not name or not (pharma_id or pharma_name):
            flash("Contract name and Pharma are required.", "danger")
            return render_template("contracts/form.html", contract=None, pharmas=pharmas)
        if pharma_id:
            pharma = Pharma.query.get_or_404(pharma_id)
        else:
            pharma = Pharma.query.filter_by(name=pharma_name).first()
            if not pharma:
                pharma = Pharma(name=pharma_name)
                db.session.add(pharma)
                db.session.flush()
        contract = Contract(name=name, pharma=pharma)
        db.session.add(contract); db.session.flush()
        if brand_ids:
            for bid in brand_ids:
                b = Brand.query.get(bid)
                if b and b.pharma_id == pharma.id:
                    contract.brands.append(b)
        else:
            for bn in [b.strip() for b in (brands_csv or '').split(',') if b.strip()]:
                b = Brand.query.filter_by(name=bn, pharma=pharma).first()
                if not b:
                    b = Brand(name=bn, pharma=pharma)
                    db.session.add(b); db.session.flush()
                contract.brands.append(b)
        db.session.commit()
        flash("Contract created.", "success")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))
    return render_template("contracts/form.html", contract=None, pharmas=pharmas)

@contracts_bp.route("/<int:contract_id>/edit", methods=["GET","POST"])
def edit_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    pharmas = Pharma.query.order_by(Pharma.name).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pharma_id = request.form.get("pharma_id", type=int)
        brand_ids = request.form.getlist("brand_ids", type=int)
        if not name or not pharma_id:
            flash("Contract name and Pharma are required.", "danger")
        else:
            contract.name = name
            pharma = Pharma.query.get_or_404(pharma_id)
            contract.pharma = pharma
            contract.brands.clear()
            for bid in brand_ids:
                b = Brand.query.get(bid)
                if b and b.pharma_id == pharma.id:
                    contract.brands.append(b)
            db.session.commit()
            flash("Contract updated.", "success")
            return redirect(url_for("contracts.view_contract", contract_id=contract.id))
    brands_selected = {b.id for b in contract.brands}
    return render_template("contracts/form.html", contract=contract, pharmas=pharmas, brands_selected=brands_selected)

# nested creates on the contract view
@contracts_bp.route("/<int:contract_id>/create-campaign", methods=["POST"])
def contract_create_campaign(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    if not name:
        flash("Campaign name is required.", "danger")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))
    c = Campaign(name=name, contract_id=contract.id, description=desc)
    db.session.add(c); db.session.commit()
    flash("Campaign created.", "success")
    return redirect(url_for("contracts.view_contract", contract_id=contract.id))

@contracts_bp.route("/<int:contract_id>/create-program", methods=["POST"])
def contract_create_program(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    name = request.form.get("name", "").strip()
    campaign_id = request.form.get("campaign_id", type=int)
    target_list_id = request.form.get("target_list_id", type=int)
    if not name or not campaign_id:
        flash("Program name and Campaign are required.", "danger")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))
    prg = Program(name=name, campaign_id=campaign_id, target_list_id=target_list_id)
    db.session.add(prg); db.session.commit()
    flash("Program created.", "success")
    return redirect(url_for("contracts.view_contract", contract_id=contract.id))

@contracts_bp.route("/<int:contract_id>/create-placement", methods=["POST"])
def contract_create_placement(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    name = request.form.get("name", "").strip()
    program_ids = request.form.getlist("program_ids", type=int)
    channel = request.form.get("channel","").strip() or None
    status = request.form.get("status","").strip() or None
    start_date = request.form.get("start_date") or None
    end_date = request.form.get("end_date") or None
    if not name or not program_ids:
        flash("Placement name and at least one Program are required.", "danger")
        return redirect(url_for("contracts.view_contract", contract_id=contract.id))
    from datetime import date
    def parse_d(s):
        try:
            return date.fromisoformat(s) if s else None
        except Exception:
            return None
    pl = Placement(name=name, channel=channel, status=status,
                   start_date=parse_d(start_date), end_date=parse_d(end_date))
    db.session.add(pl); db.session.flush()
    chosen = Program.query.filter(Program.id.in_(program_ids)).all()
    pl.programs = chosen
    db.session.commit()
    flash("Placement created.", "success")
    return redirect(url_for("contracts.view_contract", contract_id=contract.id))

# -------- Campaigns --------
@campaigns_bp.route("/")
def list_campaigns():
    page = get_page()
    per_page = get_per_page(15)
    query = Campaign.query.order_by(Campaign.id.desc())
    q = (request.args.get("q") or "").strip()
    if q:
        query = query.join(Contract).filter((Campaign.name.ilike(f"%{q}%")) | (Contract.name.ilike(f"%{q}%")))
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("campaigns/list.html", campaigns=rows, total=total, page=page, per_page=per_page, q=q)

@campaigns_bp.route("/create", methods=["GET","POST"])
def create_campaign():
    contracts = Contract.query.order_by(Contract.name).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        contract_id = request.form.get("contract_id", type=int)
        desc = request.form.get("description","").strip()
        if not name or not contract_id:
            flash("Name and Contract are required.", "danger")
        else:
            c = Campaign(name=name, contract_id=contract_id, description=desc)
            db.session.add(c); db.session.commit()
            return redirect(url_for("campaigns.list_campaigns"))
    return render_template("campaigns/form.html", contracts=contracts, campaign=None)

@campaigns_bp.route("/<int:campaign_id>/edit", methods=["GET","POST"])
def edit_campaign(campaign_id):
    c = Campaign.query.get_or_404(campaign_id)
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
    page = get_page()
    per_page = get_per_page(15)
    query = Program.query.order_by(Program.id.desc())
    q = (request.args.get("q") or "").strip()
    if q:
        query = query.join(Campaign).filter((Program.name.ilike(f"%{q}%")) | (Campaign.name.ilike(f"%{q}%")))
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("programs/list.html", programs=rows, total=total, page=page, per_page=per_page, q=q)

@programs_bp.route("/create", methods=["GET","POST"])
def create_program():
    campaigns = Campaign.query.order_by(Campaign.name).all()
    tls = TargetList.query.order_by(TargetList.uploaded_at.desc()).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        campaign_id = request.form.get("campaign_id", type=int)
        target_list_id = request.form.get("target_list_id", type=int)
        if not name or not campaign_id:
            flash("Name and Campaign are required.", "danger")
        else:
            prg = Program(name=name, campaign_id=campaign_id, target_list_id=target_list_id)
            db.session.add(prg); db.session.commit()
            return redirect(url_for("programs.list_programs"))
    return render_template("programs/form.html", program=None, campaigns=campaigns, target_lists=tls)

@programs_bp.route("/<int:program_id>/edit", methods=["GET","POST"])
def edit_program(program_id):
    program = Program.query.get_or_404(program_id)
    campaigns = Campaign.query.order_by(Campaign.name).all()

    if request.method == "POST":
        program.name = request.form.get("name","").strip()
        program.campaign_id = request.form.get("campaign_id", type=int)
        program.target_list_id = request.form.get("target_list_id", type=int)
        db.session.commit()
        nxt = request.form.get("next") or request.args.get("next")
        if nxt:
            return redirect(nxt)
        return redirect(url_for("programs.list_programs"))
    
    # --- prefilter by program's campaign -> contract (pharma & brands) ---
    filtered_tls = []
    if program.campaign_id:
        camp = Campaign.query.get(program.campaign_id)
        contract = Contract.query.get(camp.contract_id) if camp else None
        if contract:
            pharma_id = contract.pharma_id
            brand_ids = [b.id for b in contract.brands]
            if pharma_id and brand_ids:
                filtered_tls = (TargetList.query
                                .filter(
                                    TargetList.pharmas.any(Pharma.id == pharma_id),
                                    TargetList.brands.any(Brand.id.in_(brand_ids))
                                )
                                .order_by(TargetList.label)
                                .all())

    # make sure the currently selected TL is present
    if program.target_list_id and all(tl.id != program.target_list_id for tl in filtered_tls):
        cur = TargetList.query.get(program.target_list_id)
        if cur:
            filtered_tls.append(cur)
    filtered_tls = sorted(filtered_tls, key=lambda t: (t.label or "").lower())

    return render_template(
        "programs/form.html",
        program=program,
        campaigns=campaigns,
        target_lists=filtered_tls,  # template can preload these
    )

# -------- Placements (M2M) --------
@placements_bp.route("/")
def list_placements():
    page = get_page()
    per_page = get_per_page(15)
    query = Placement.query.order_by(Placement.id.desc())
    q = (request.args.get("q") or "").strip()
    if q:
        query = query.filter(Placement.name.ilike(f"%{q}%"))
    total = query.count()
    rows = query.offset((page-1)*per_page).limit(per_page).all()
    return render_template("placements/list.html", placements=rows, total=total, page=page, per_page=per_page, q=q)

@placements_bp.route("/create", methods=["GET","POST"])
def create_placement():
    programs = Program.query.order_by(Program.name).all()
    if request.method == "POST":
        name = request.form.get("name","").strip()
        program_ids = request.form.getlist("program_ids", type=int)
        channel = request.form.get("channel","").strip() or None
        status = request.form.get("status","").strip() or None
        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None
        if not name or not program_ids:
            flash("Name and at least one Program are required.", "danger")
        else:
            from datetime import date
            def parse_d(s):
                try:
                    return date.fromisoformat(s) if s else None
                except Exception:
                    return None
            pl = Placement(name=name, channel=channel, status=status,
                           start_date=parse_d(start_date), end_date=parse_d(end_date))
            db.session.add(pl); db.session.flush()
            if program_ids:
                chosen = Program.query.filter(Program.id.in_(program_ids)).all()
                pl.programs = chosen
            db.session.commit()
            flash("Placement created.", "success")
            return redirect(url_for("placements.list_placements"))
    return render_template("placements/form.html", programs=programs, placement=None, selected_program_ids=set())

@placements_bp.route("/<int:placement_id>/edit", methods=["GET","POST"])
def edit_placement(placement_id):
    pl = Placement.query.get_or_404(placement_id)
    programs = Program.query.order_by(Program.name).all()

    def _parse_date(s):
        from datetime import date
        try:
            return date.fromisoformat(s) if s else None
        except Exception:
            return None

    if request.method == "POST":
        pl.name = request.form.get("name","").strip()
        program_ids = request.form.getlist("program_ids", type=int)
        pl.channel = request.form.get("channel","").strip() or None
        pl.status = request.form.get("status","").strip() or None
        pl.start_date = _parse_date(request.form.get("start_date"))
        pl.end_date = _parse_date(request.form.get("end_date"))
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

        nxt = request.form.get("next") or request.args.get("next")
        if nxt:
            return redirect(nxt)
        return redirect(url_for("placements.list_placements"))

    selected_program_ids = {p.id for p in pl.programs}
    return render_template("placements/form.html", programs=programs, placement=pl, selected_program_ids=selected_program_ids)


