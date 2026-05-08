import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

Base = declarative_base()

class Database:
    def __init__(self, db_url):
        kwargs = {}
        if db_url.startswith("oracle"):
            default_wallet_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'wallet')
            wallet_path = os.getenv("ORACLE_WALLET_PATH", default_wallet_path)

            kwargs ["connect_args"]= {
                    "config_dir": wallet_path,
                    "wallet_location": wallet_path,
                    "wallet_password": os.getenv("DB_WALLET_PASSWORD"),
                }

        self.engine = create_engine(db_url, **kwargs)
        self.session = scoped_session(sessionmaker(bind=self.engine))

    def init_db(self):
        Base.metadata.create_all(self.engine)

    def test_connection(self):
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return f"Successfully connected. Tables: {tables}"
        except Exception as e:
            return f"Error testing database connection: {e}"


db = Database(os.getenv("DATABASE_URL"))