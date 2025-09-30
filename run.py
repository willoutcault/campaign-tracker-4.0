
import os
from app import create_app, db
from flask import current_app

app = create_app()

@app.cli.command("db-init")
def db_init():
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")

@app.cli.command("migrate-m2m-placements")
def migrate_m2m_placements():
    from sqlalchemy import text
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Detect if program_id column exists
            info = conn.execute(text("PRAGMA table_info(placement)")).fetchall()
            has_program_id = any(row[1] == 'program_id' for row in info)
            if not has_program_id:
                print("No 'program_id' column found on placement — nothing to migrate.")
                trans.commit()
                return

            print("Creating join table program_placement (if not exists)...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS program_placement (
                    program_id INTEGER NOT NULL,
                    placement_id INTEGER NOT NULL,
                    PRIMARY KEY (program_id, placement_id),
                    FOREIGN KEY (program_id) REFERENCES program(id),
                    FOREIGN KEY (placement_id) REFERENCES placement(id)
                );
            """))

            print("Backfilling mappings from placement.program_id -> program_placement...")
            conn.execute(text("""
                INSERT OR IGNORE INTO program_placement (program_id, placement_id)
                SELECT program_id, id FROM placement WHERE program_id IS NOT NULL;
            """))

            print("Rebuilding placement table without program_id...")
            conn.execute(text("PRAGMA foreign_keys=off;"))
            conn.execute(text("""
                CREATE TABLE placement_new (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    channel VARCHAR(100),
                    status VARCHAR(50),
                    start_date DATE,
                    end_date DATE
                );
            """))
            conn.execute(text("""
                INSERT INTO placement_new (id, name, channel, status, start_date, end_date)
                SELECT id, name, channel, status, start_date, end_date FROM placement;
            """))
            conn.execute(text("DROP TABLE placement;"))
            conn.execute(text("ALTER TABLE placement_new RENAME TO placement;"))
            conn.execute(text("PRAGMA foreign_keys=on;"))
            trans.commit()
            print("✓ Migration complete.")
        except Exception as e:
            print("Migration failed:", e)
            trans.rollback()
            raise

if __name__ == "__main__":
    app.run(debug=True)

