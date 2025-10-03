
from __future__ import with_statement
from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine

# interpret the config file for Python logging.
config = context.config
fileConfig(config.config_file_name)

# Get DB URL from env or default to SQLite in instance/
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.strip() == "":
    # attempt to use instance/app.db relative path
    instance_path = os.path.join(os.getcwd(), "instance")
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, "app.sqlite")
    DATABASE_URL = f"sqlite:///{db_path}".replace('\\','/')

def run_migrations_offline():
    url = DATABASE_URL
    context.configure(
        url=url, target_metadata=None, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
