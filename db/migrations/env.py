import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from db.postgres import Base

config = context.config
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read URL directly from env — bypasses configparser which chokes on % in passwords
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://memos:vishnu%40memos%40rag@localhost:5432/memos")


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
