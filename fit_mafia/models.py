from sqlalchemy import Column, String
from sqlalchemy.orm import class_mapper
import datetime
from sqlalchemy import case
from sqlalchemy.ext.hybrid import hybrid_property
from fit_mafia.db import Base, db

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
            end_date = datetime.date.fromisoformat(str(self.subscription_end_date))
            return 'active' if end_date >= datetime.date.today() else 'expired'
        except (ValueError, TypeError):
        # If date is invalid, treat as expired
            return 'expired'

    @status.expression
    def status(cls): # noqa: N805
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

# Ensure tables are created when importing models
db.init_db()
