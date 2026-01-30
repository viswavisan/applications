# language: python
import os
import sys
import glob
import contextlib
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

alembic_cfg = Config(str(project_root / "migrations" / "alembic.ini"))


def _is_revision_empty() -> bool:
    try:
        db_url = alembic_cfg.get_main_option("sqlalchemy.url") or ""
        if not db_url:
            return True
        try:
            from Interview_evaluation.models import Base  # noqa: WPS433
        except Exception:
            return True
        engine = create_engine(db_url)
        with engine.connect() as conn:
            mc = MigrationContext.configure(connection=conn, opts={"target_metadata": Base.metadata})
            diffs = compare_metadata(mc, Base.metadata)
            return len(diffs) == 0
    except Exception:
        return True


def main() -> None:
    print("Creating revision...")
    command.revision(alembic_cfg, message="baseline schema", autogenerate=True)


    versions_dir = project_root / "migrations" / "versions"
    pattern = str(versions_dir / "*_baseline_schema.py")
    matches = sorted(glob.glob(pattern), key=os.path.getmtime)
    if not matches:
        raise FileNotFoundError(f"No revision file found for pattern: {pattern}")
    revision_py = Path(matches[-1])
    revision_base = revision_py.stem

    if _is_revision_empty():
        print("No schema changes detected; removing empty revision:", revision_py)
        try:
            revision_py.unlink()
            print("Revision removed:", revision_py)
            return
        except OSError as exc:
            print("Failed to remove empty revision:", exc)
            return

    print("Generating SQL...")
    sql_output = versions_dir / f"{revision_base}.sql"
    sql_output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(sql_output, "w", encoding="utf-8") as f:
            with contextlib.redirect_stdout(f):
                command.upgrade(alembic_cfg, "head", sql=True)
        print("SQL written to", sql_output)
    except Exception as exc:
        print("Failed to generate SQL:", exc)
        return

    print("Upgrading to head (applying migrations)...")
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        print("Failed to apply migrations:", exc)
        return

    print("Done.")


if __name__ == "__main__":
    main()