from flask import request, jsonify
from ..extensions import db
from ..models import Campaign, Contract, Pharma, Brand, TargetList
from .campaigns_programs import programs_bp

@programs_bp.route("/api/target-lists")
def api_program_target_lists():
    if request.args.get("all") == "1":
        tls = TargetList.query.order_by(TargetList.label).all()
        return jsonify([{"id": tl.id, "label": tl.label} for tl in tls])

    campaign_id   = request.args.get("campaign_id", type=int)
    current_tl_id = request.args.get("current_tl_id", type=int)
    if not campaign_id:
        return jsonify([])

    camp = Campaign.query.get_or_404(campaign_id)
    contract = Contract.query.get_or_404(camp.contract_id)
    pharma_id = contract.pharma_id
    brand_ids = [b.id for b in contract.brands]

    tls = []
    if pharma_id and brand_ids:
        tls = (TargetList.query
               .filter(
                 TargetList.pharmas.any(Pharma.id == pharma_id),
                 TargetList.brands.any(Brand.id.in_(brand_ids))
               )
               .order_by(TargetList.label)
               .all())

    if current_tl_id and all(t.id != current_tl_id for t in tls):
        cur = TargetList.query.get(current_tl_id)
        if cur:
            tls.append(cur)

    tls.sort(key=lambda x: (x.label or '').lower())
    return jsonify([{"id": t.id, "label": t.label} for t in tls])
