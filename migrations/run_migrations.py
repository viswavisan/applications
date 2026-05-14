import os
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

class MigrationManager:
    def __init__(self, ini_filename="alembic.ini"):
        # Get the directory where this script is located (the migrations folder)
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.alembic_ini_path = os.path.join(self.script_dir, ini_filename)
        self.alembic_cfg = Config(self.alembic_ini_path)

    def create_revision(self, message="new_revision"):
        # Ensure the database is up-to-date before autogenerating
        print("Upgrading database to 'head' before creating a new revision...")
        try:
            command.upgrade(self.alembic_cfg, "head")
        except Exception as e:
            if "Can't locate revision identified by" in str(e):
                print("Missing revision detected. Syncing database version to local 'head'...")
                db_url = os.getenv("DATABASE_URL") or self.alembic_cfg.get_main_option("sqlalchemy.url")
                engine = create_engine(db_url)
                with engine.begin() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                command.stamp(self.alembic_cfg, "head")
            else:
                print(f"Could not cleanly upgrade. Proceeding anyway... ({e})")
            
        print(f"Generating new migration revision: '{message}'...")
        script = command.revision(self.alembic_cfg, autogenerate=True, message=message)
        if script:
            print("Revision generated successfully!")
        else:
            print("No new revision was generated (no changes detected).")

    def upgrade(self, revision="head"):
        print(f"Running database migrations to '{revision}'...")
        command.upgrade(self.alembic_cfg, revision)
        print("upgrade complete!")

    def downgrade(self, revision="-1"):
        print(f"Downgrading database migrations to '{revision}'...")
        command.downgrade(self.alembic_cfg, revision)
        print("Downgrade complete!")

    def stamp(self, revision="head"):
        print(f"Forcibly stamping the database to '{revision}'...")
        command.stamp(self.alembic_cfg, revision)
        print("Stamp complete!")

if __name__ == "__main__":
    manager = MigrationManager()
    # manager.create_revision("")
    # manager.upgrade()
