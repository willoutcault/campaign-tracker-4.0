import os
from app import create_app, db

app = create_app()

@app.cli.command("db-init")
def db_init():
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")

@app.cli.command("upgrade-schema-v12")
def upgrade_schema_v12():
    from sqlalchemy import text
    with app.app_context():
        conn = db.engine.connect()
        def has_column(table, col):
            rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            return any(r[1] == col for r in rows)

        def add_col(table, col_def):
            print(f"Adding {table}.{col_def} ...")
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_def};"))

        # Contract columns
        for col, ddl in [
            ('contract_number', 'contract_number VARCHAR(100)'),
            ('start_date', 'start_date DATE'),
            ('end_date', 'end_date DATE'),
            ('signed_date', 'signed_date DATE'),
            ('budget_total', 'budget_total REAL'),
            ('billing_terms', 'billing_terms VARCHAR(50)'),
            ('status', 'status VARCHAR(30)'),
            ('notes', 'notes TEXT'),
            ('created_by', 'created_by VARCHAR(120)'),
            ('last_modified_by', 'last_modified_by VARCHAR(120)'),
        ]:
            if not has_column('contract', col):
                add_col('contract', ddl)

        # Campaign columns
        for col, ddl in [
            ('campaign_code', 'campaign_code VARCHAR(100)'),
            ('start_date', 'start_date DATE'),
            ('end_date', 'end_date DATE'),
            ('launch_date', 'launch_date DATE'),
            ('objective', 'objective VARCHAR(120)'),
            ('channel_mix', 'channel_mix TEXT'),
            ('status', 'status VARCHAR(30)'),
            ('kpi_goals', 'kpi_goals TEXT'),
        ]:
            if not has_column('campaign', col):
                add_col('campaign', ddl)

        # Program columns
        for col, ddl in [
            ('program_code', 'program_code VARCHAR(100)'),
            ('start_date', 'start_date DATE'),
            ('end_date', 'end_date DATE'),
            ('launch_date', 'launch_date DATE'),
            ('program_type', 'program_type VARCHAR(120)'),
            ('content_type', 'content_type VARCHAR(120)'),
            ('audience_segment', 'audience_segment VARCHAR(120)'),
            ('status', 'status VARCHAR(30)'),
            ('expected_reach', 'expected_reach INTEGER'),
            ('notes', 'notes TEXT'),
        ]:
            if not has_column('program', col):
                add_col('program', ddl)

        # Placement columns
        for col, ddl in [
            ('placement_code', 'placement_code VARCHAR(100)'),
            ('format', 'format VARCHAR(100)'),
            ('frequency_cap', 'frequency_cap INTEGER'),
            ('ad_server', 'ad_server VARCHAR(100)'),
            ('impression_goal', 'impression_goal INTEGER'),
            ('click_goal', 'click_goal INTEGER'),
        ]:
            if not has_column('placement', col):
                add_col('placement', ddl)

        print("✓ upgrade-schema-v12 completed")
        conn.close()

# Hotfix 15: add CLI to create join tables
@app.cli.command("upgrade-schema-v15")
def upgrade_schema_v15():
    """Create pharma_target_list and brand_target_list tables if they don't exist."""
    from sqlalchemy import text
    with app.app_context():
        conn = db.engine.connect()
        def has_table(name):
            rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"), {"n": name}).fetchall()
            return len(rows) > 0
        if not has_table("pharma_target_list"):
            conn.execute(text("""
                CREATE TABLE pharma_target_list (
                    pharma_id INTEGER NOT NULL,
                    target_list_id INTEGER NOT NULL,
                    PRIMARY KEY (pharma_id, target_list_id),
                    FOREIGN KEY(pharma_id) REFERENCES pharma (id),
                    FOREIGN KEY(target_list_id) REFERENCES target_list (id)
                );
            """))
            print("✓ Created table pharma_target_list")
        if not has_table("brand_target_list"):
            conn.execute(text("""
                CREATE TABLE brand_target_list (
                    brand_id INTEGER NOT NULL,
                    target_list_id INTEGER NOT NULL,
                    PRIMARY KEY (brand_id, target_list_id),
                    FOREIGN KEY(brand_id) REFERENCES brand (id),
                    FOREIGN KEY(target_list_id) REFERENCES target_list (id)
                );
            """))
            print("✓ Created table brand_target_list")
        conn.close()
        print("✓ upgrade-schema-v15 completed")

if __name__ == "__main__":
    app.run(debug=True)