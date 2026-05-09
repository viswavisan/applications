import os
from alembic.config import Config
from alembic import command

def run_migrations():
    # Get the directory where this script is located (the migrations folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_ini_path = os.path.join(script_dir, "alembic.ini")
    
    alembic_cfg = Config(alembic_ini_path)
    print("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete!")

if __name__ == "__main__":
    run_migrations()
