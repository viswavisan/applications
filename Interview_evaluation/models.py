from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, declarative_base, sessionmaker

Base = declarative_base()

class Database:
    def __init__(self, db_url="sqlite:///interview.db"):
        self.engine = create_engine(db_url)
        # scoped_session creates a thread-local session
        self.session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.create_all(self.engine)

class Answer(Base):
    __tablename__ = 'answers'
    applicant_id = Column(Integer, primary_key=True)
    applicant_name = Column(String, nullable=True)
    questions = Column(String, nullable=True)
    answers = Column(String, nullable=True)

db = Database()
