
from flask import request
from sqlalchemy import or_

def get_page(default=1):
    try:
        return max(int(request.args.get("page", default)), 1)
    except Exception:
        return default

def get_per_page(default=10, max_per=100):
    try:
        per = int(request.args.get("per_page", default))
        return min(max(per, 1), max_per)
    except Exception:
        return default

def apply_search(query, model, fields):
    q = (request.args.get("q") or "").strip()
    if not q:
        return query, q
    clauses = []
    for f in fields:
        clauses.append(getattr(model, f).ilike(f"%{q}%"))
    return query.filter(or_(*clauses)), q
