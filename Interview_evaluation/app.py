import json
import sys
import io
import os
from flask import Flask, render_template, Blueprint, request
from flask_smorest import Blueprint
try:
    from .models import db, Answer
    from .questions import questions
    from .schemas import AnswerSchema
except ImportError:
    from models import db, Answer
    from questions import questions
    from schemas import AnswerSchema

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Blueprint('Evaluation', __name__, template_folder=template_dir)


@app.route('/run', methods=['POST'])
def run():
    code = request.get_data(as_text=True)
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    try:
        exec(code, {})
        output = redirected_output.getvalue()
    except Exception as e:
        output = str(e)
    finally:
        sys.stdout = old_stdout

    return output


@app.route('/register', methods=['POST', 'GET'])
def register():
    try:
        data = request.get_json(silent=True) or {}

        # Create new record with questions from questions.py
        new_record = Answer()
        new_record.questions = json.dumps(questions)
        new_record.applicant_name = data.get('name','xxxxx')
        db.session.add(new_record)
        db.session.commit()
        return str(new_record.applicant_id)

    except Exception as e:
        return str(e)


@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    try:
        data = request.get_json()
        record = db.session.get(Answer, int(data['applicant_id']))
        questions_json=json.loads(record.questions)
        for question in questions_json:
            question['answer']=data['answers'][str(question['id'])]
        record.questions = json.dumps(questions_json)
        db.session.commit()
        return 'thanks'
    except Exception as e:
        return str(e)


@app.route("/evaluate/<int:candidate_id>", methods=["GET"])
@app.response(200, AnswerSchema)
def evaluate(candidate_id):
    try:
        candidate = db.session.get(Answer, candidate_id)
        if not candidate:
            return "Candidate is not registered please contact admin"
        try:
            questions_value = json.loads(candidate.questions or '{}')
        except (json.JSONDecodeError, TypeError):
            questions_value = {}

        payload = {
            "applicant_name": candidate.applicant_name,
            "applicant_id": candidate.applicant_id,
            "questions": questions_value
        }
        return render_template("evaluate.html", payload=payload)
    except Exception as e:
        return str(e)

@app.route("/admin", methods=["GET"])
def admin():
    # Admin dashboard logic
    return render_template("admin.html")




if __name__ == "__main__":
    mainapp = Flask(__name__)
    mainapp.register_blueprint(app)
    mainapp.run(host='127.0.0.1', port=5000, debug=True)
