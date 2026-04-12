from sqlalchemy import create_engine, Column, String, text
from sqlalchemy.orm import scoped_session, declarative_base, sessionmaker
import os

Base = declarative_base()

class Database:
    def __init__(self, db_url= None):
        if db_url is None:
            local_db_path = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fitmafia.db')}"
            db_url = os.getenv("DATABASE_URL", local_db_path)
        self.engine = create_engine(db_url)
        # scoped_session creates a thread-local session
        self.session = scoped_session(sessionmaker(bind=self.engine))

        # Ensure the schema exists before creating tables
        if db_url.startswith("postgresql"):
            with self.engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS fitmafia"))
                conn.commit()  # Required for SQLAlchemy 2.0+ DDL execution
                
        Base.metadata.create_all(self.engine)

class Session(Base):
    __tablename__ = 'session'
    __table_args__ = {'schema': 'fitmafia'}
    session_id = Column(String, primary_key=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    user_name = Column(String, nullable=True)

class Member(Base):
    __tablename__ = 'member'
    __table_args__ = {'schema': 'fitmafia'}
    mobile_number = Column(String, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    bmi = Column(String, nullable=True)
    subscription = Column(String, nullable=True)
    joining_date = Column(String, nullable=True)
    photo = Column(String, nullable=True)


db = Database()