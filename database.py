from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy.schema import CreateTable

from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext

import pandas as pd

Base = declarative_base()

class Database:
    def __init__(self, db_url):
        kwargs = {}
        self.is_oracle = db_url and db_url.startswith("oracle")
        if self.is_oracle:
            default_wallet_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'wallet')
            wallet_path = os.getenv("ORACLE_WALLET_PATH", default_wallet_path)

            kwargs ["connect_args"]= {
                    "config_dir": wallet_path,
                    "wallet_location": wallet_path,
                    "wallet_password": os.getenv("DB_WALLET_PASSWORD"),
                }
        elif db_url and db_url.startswith("postgres"):
            kwargs["connect_args"] = {"options": "-c search_path=fitmafia"}

        self.engine = create_engine(db_url, **kwargs)
        self.session = scoped_session(sessionmaker(bind=self.engine))

    def init_db(self):
        """creates all tables from model if not already present"""
        Base.metadata.create_all(self.engine)

    def test_connection(self):
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return f"Successfully connected. Tables: {tables}"
        except Exception as e:
            return f"Error testing database connection: {e}"

    def get_sql_schema(self):
        """Print SQL schema from model definition"""
        schema_statements = []
        if not self.is_oracle:
            schema_statements.append("BEGIN;")

        for table in Base.metadata.sorted_tables:
            statement = str(CreateTable(table).compile(self.engine))
            schema_statements.append(statement + ";")
        
        if not self.is_oracle:
            schema_statements.append("COMMIT;")

        final_statements="\n\n".join(schema_statements)
        return final_statements

    def get_sql_schema_diffs(self):
        conn = self.engine.connect()
        context = MigrationContext.configure(conn)
        diffs = produce_migrations(context, Base.metadata)
        
        statements = []
        if not self.is_oracle:
            statements.append("BEGIN;")

        for op in diffs.upgrade_ops.ops:
            if hasattr(op, 'table_name') and op.table_name == 'dbtools$execution_history':
                continue
            cname = op.__class__.__name__

            if cname == "ModifyTableOps":
                for subop in op.ops:
                    subname = subop.__class__.__name__
                    if subname == "AlterColumnOp":
                        new_type = str(getattr(subop, "modify_type").compile(dialect=self.engine.dialect))
                        if self.is_oracle:
                            sql = f"ALTER TABLE {subop.table_name} MODIFY {subop.column_name} {new_type};"
                        else:
                            sql = f"ALTER TABLE {subop.table_name} ALTER COLUMN {subop.column_name} TYPE {new_type};"
                        statements.append(sql)
                    elif subname == "AddColumnOp":
                        sql = f"ALTER TABLE {subop.table_name} ADD COLUMN {subop.column.name} {subop.column.type.compile(self.engine.dialect)};"
                        statements.append(sql)
                    elif subname == "DropColumnOp":
                        sql = f"ALTER TABLE {subop.table_name} DROP COLUMN {subop.column_name};"
                        statements.append(sql)

            elif cname == "DropTableOp":
                sql = f"DROP TABLE {op.table_name};"
                statements.append(sql)

            elif cname == "CreateTableOp":
                from sqlalchemy.schema import CreateTable
                ddl = str(CreateTable(op.table).compile(self.engine))
                statements.append(ddl + ";")
        
        if not self.is_oracle:
            statements.append("COMMIT;")

        final_statements="\n".join(statements)
        conn.close()
        return final_statements

    def run_sql(self, sql_command):
        """Runs a SQL command and returns the result"""
        try:
            with self.engine.connect() as connection:
                # Each command must be executed separately. Split by semicolon.
                commands = [cmd.strip() for cmd in sql_command.split(';') if cmd.strip()]
                results = []
                # Use a transaction for non-Oracle DBs
                trans = connection.begin() if not self.is_oracle else None
                try:
                    for command in commands:
                        # Skip transaction control commands if we are managing the transaction
                        if command.upper() in ('BEGIN', 'COMMIT') and trans:
                            continue
                        print(command)
                        result = connection.execute(text(command))
                        if result.returns_rows:
                            results.extend(result.fetchall())
                    if trans:
                        trans.commit()
                    if results:
                        return results
                    else:
                        return "Command executed successfully."
                except Exception:
                    if trans:
                        trans.rollback()
                    raise
        except Exception as e:
            return f"Error running SQL command: {e}"

def migrate_data(source_db_url, dest_db_url, tables=None):
    source_db = Database(source_db_url)
    dest_db = Database(dest_db_url)
    print("Starting data migration...")
    try:
        # 1. Create schema in destination if it doesn't exist
        dest_db.init_db()
        print("Destination schema initialized.")

        # 2. Get table names from the source database
        if tables is None:
            inspector = inspect(source_db.engine)
            tables_to_migrate = inspector.get_table_names()
            print(f"Found all tables in source: {tables_to_migrate}")
        else:
            tables_to_migrate = tables
            print(f"Tables to migrate: {tables_to_migrate}")

        # 3. For each table, copy data
        for table_name in tables_to_migrate:
            print(f"Migrating table: {table_name}")

            try:
                # Read data from source into a pandas DataFrame
                source_query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(source_query, source_db.engine)

                if not df.empty:
                    # Write data to destination
                    df.to_sql(table_name, dest_db.engine, if_exists='append', index=False)
                    print(f"  - Copied {len(df)} rows to {table_name}.")
                else:
                    print(f"  - Table {table_name} is empty, skipping.")
            except Exception as table_error:
                print(f"  - Error migrating table {table_name}: {table_error}")

        print("Data migration completed successfully!")

    except Exception as e:
        print(f"An error occurred during data migration: {e}")

if __name__ == '__main__':
    migrate_data(os.getenv("PG_DATABASE_URL"), os.getenv("OCI_DATABASE_URL"),['transaction'])