from flask import Flask, render_template
from flask import request
import json,sys,io

app = Flask(__name__)

# SQLAlchemy setup
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
Base = declarative_base()

#Define database connection and session
class Database:
    def __init__(self, db_url="sqlite:///interview.db"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = self.Session()

#Define table structure
class Answer(Base):
    __tablename__ = 'answers'
    applicant_id = Column(Integer, primary_key=True)
    applicant_name = Column(String, nullable=False)
    questions = Column(String, nullable=False)
    answers = Column(String, nullable=False)


# Initialize the database
db = Database()

@app.route('/run',methods=['POST'])
def run():
    code=request.get_data()
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    try:
        exec(code,{})
        output = redirected_output.getvalue()
    except Exception as e:
        output = str(e)

    sys.stdout = old_stdout
    return output

@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    data = request.get_json()
    record = db.session.get(Answer, int(data['applicant_id']))
    record.answers=json.dumps(data['answers'])
    questions_dict = json.loads(record.questions)
    for key, value in data['answers'].items():
        questions_dict[key]["answer"] = value 
    record.questions = json.dumps(questions_dict)
    db.session.commit()
            



    print("Received Answers:")  # Optional debug
    return 'thanks'



@app.route("/evaluate/<int:id>", methods=["GET"])
def evaluate(id):
    candidate = db.session.get(Answer, id)
    print(id)
    if not candidate: return "Candidate is not registered please contact admin"
    return render_template("evaluate.html", payload={
        "applicant_name": candidate.applicant_name,
        "applicant_id": candidate.applicant_id,
        "questions": json.loads(candidate.questions)
    })

@app.route("/admin", methods=["GET"])
def admin():
    # Admin dashboard logic
    return render_template("admin.html")

@app.route("/submit_answers", methods=["POST"])
def submit_answers():
    #get the applicant_id, applicant_name and questions from the request body
    request_data = request.get_json()
    applicant_id = int(request_data.get('applicant_id'))
    applicant_name = request_data.get('applicant_name')
    questions = request_data.get('questions')
    questions = json.dumps(questions)
    print(questions)
    save_answers(applicant_id, applicant_name, questions)
    return 'Answers submitted successfully!'

def save_answers(applicant_id, applicant_name, questions):
    #insert if id not exists, else update
    existing_answer = db.session.get(Answer, applicant_id)
    if existing_answer:
        existing_answer.applicant_name = applicant_name
        existing_answer.questions = questions
    else:
        db.session.add(Answer(applicant_id=applicant_id, applicant_name=applicant_name, questions=questions))
    db.session.commit()
    return 'saved successfully'

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
