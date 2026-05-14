import os
import datetime
from sqlalchemy import engine_from_config, pool
from alembic import context

from fit_mafia.db import Base 
import fit_mafia.models
target_metadata = Base.metadata

from logging.config import fileConfig

DATABASE_URL = os.getenv("DATABASE_URL")

config = context.config
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def process_revision_directives(context, revision, directives):
    """Set the revision ID to a timestamp in yyyymmddhhmmss format."""
    if directives and getattr(directives[0], 'upgrade_ops', None) is not None:
        if directives[0].upgrade_ops.is_empty():
            print("No changes in schema detected. Skipping revision generation.")
            directives[:] = []
            return

    for directive in directives:
        directive.rev_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == "fitmafia"
    else:
        return True


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
        include_schemas=True,   # important!
        include_name=include_name,
        version_table_schema="fitmafia"  
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            include_schemas=True,   # important!
            include_name=include_name,
            version_table_schema="fitmafia"  
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
