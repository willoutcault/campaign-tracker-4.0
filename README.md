# Campaign Tracker 4.0 (MVP)

A clean, minimal Flask app with SQLite + S3 that tracks Clients, Target Lists, Contracts → Campaigns → Programs → Placements.

## Features
- **Clients**: create/edit (SQLite).
- **Target Lists**: upload to S3; metadata saved in SQLite.
- **Contracts**: map to Pharma and one or more Brands.
- **Hierarchy**: Contract → Campaign(s) → Program(s) → Placement(s).
- **Program ↔ Target List**: each Program maps to exactly one Target List (and can be updated).

## Quickstart
1. Create and activate a virtual env: `python -m venv .venv && . .venv/Scripts/activate` #Windows
2. Install: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.
4. Initialize DB: `python run.py db-init`
5. Run dev server: `python run.py` then open http://127.0.0.1:5000/

SQLite file will be created at `instance/app.db`.
