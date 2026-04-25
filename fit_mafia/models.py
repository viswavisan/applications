from sqlalchemy import create_engine, Column, String, text, Boolean
from sqlalchemy.orm import scoped_session, declarative_base, sessionmaker, class_mapper
import os
import datetime
from sqlalchemy import case
from sqlalchemy.ext.hybrid import hybrid_property

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
    gender = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    bmi = Column(String, nullable=True)
    subscription = Column(String, nullable=True)
    joining_date = Column(String, nullable=True)
    subscription_start_date = Column(String, nullable=True)
    subscription_end_date = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    password = Column(String, nullable=True)

    @hybrid_property
    def status(self):
        """Calculates status in Python code."""
        if not self.subscription_end_date:
            return 'expired'
        
        try:
            end_date = datetime.date.fromisoformat(self.subscription_end_date)
            return 'active' if end_date >= datetime.date.today() else 'expired'
        except (ValueError, TypeError):
            # If date is invalid, treat as expired
            return 'expired'

    @status.expression
    def status(cls):
        """Generates the SQL expression for status queries."""
        today_str = datetime.date.today().isoformat()
        return case(
            (cls.subscription_end_date == None, 'expired'),
            (cls.subscription_end_date < today_str, 'expired'),
            else_='active'
        )

    def to_dict(self):
        """Return a dictionary representation of the model, excluding the password."""
        column_dict = {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns if c.key != 'password'}
        column_dict['status'] = self.status # Manually add the hybrid property
        return column_dict

class Transaction(Base):
    __tablename__ = 'transaction'
    __table_args__ = {'schema': 'fitmafia'}
    transaction_id = Column(String, primary_key=True)
    member_name = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    date = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    discount = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    status = Column(String, nullable=True)


db = Database()
