import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Setup Alembic configuration
config = context.config

# 3. Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Import your Base and Models
# Ensure 'app' is in your PYTHONPATH or run alembic from the project root
from app.database import Base
from app import models  # This must contain 'class User(Base): ...'

# Set the target metadata for autogenerate
target_metadata = Base.metadata

def get_url():
    """Retrieve the URL from .env and ensure it is valid."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set for Alembic")
    # Handle the '@' in password if not already encoded in .env
    if "@" in url.split('://')[1].split('@')[0]:
        # This is a fallback, ideally encode it directly in your .env as %40
        pass 
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (Direct DB connection)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Removed 'include_schemas' locks to allow local public schema management
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
