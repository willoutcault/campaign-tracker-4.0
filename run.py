import os
from app import create_app, db
from flask import current_app

app = create_app()

@app.cli.command("db-init")
def db_init():
    """Create database tables."""
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")

if __name__ == "__main__":
    app.run(debug=True)
