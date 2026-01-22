from flask import Flask, render_template, redirect
from flask import request
import json,sys,io
from flask_smorest import Api
from models import db, Answer

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(e):
    # Gather all registered endpoints
    rules = []
    for rule in app.url_map.iter_rules():
        # Filter out internal methods like HEAD/OPTIONS for cleaner output
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        rules.append(f"<li><b>{rule.rule}</b> [{methods}]</li>")

    return f"""
     <h3>Page not found (404)</h3>
     <p>The requested URL was not found. Here are the available endpoints:</p>
     <ul>{''.join(sorted(rules))}</ul>
     {e}
     """, 404


app.config["API_TITLE"] = "My API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

@app.route("/")
def home():
    return redirect("/docs")

# Flask teardown to remove session after request
@app.teardown_appcontext
def shutdown_session(exception=None):
    print(exception)
    db.session.remove()

@app.route('/run',methods=['POST'])
def run():
    code=request.get_data(as_text=True)
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
    try:
        data = request.get_json()
        record = db.session.get(Answer, int(data['applicant_id']))
        record.answers=json.dumps(data['answers'])
        questions_dict = json.loads(record.questions)
        for key, value in data['answers'].items():
            questions_dict[key]["answer"] = value
        record.questions = json.dumps(questions_dict)
        db.session.commit()
        return 'thanks'
    except Exception as e:
        return str(e)


@app.route("/evaluate/<int:candidate_id>", methods=["GET"])
def evaluate(candidate_id):
    candidate = db.session.get(Answer, candidate_id)
    if not candidate: return "Candidate is not registered please contact admin"
    return render_template("evaluate.html", payload={
        "applicant_name": candidate.applicant_name,
        "applicant_id": candidate.applicant_id,
        "questions": json.loads(str(candidate.questions))
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
    save_answers(applicant_id, applicant_name, questions)
    return 'Answers submitted successfully!'

def save_answers(applicant_id, applicant_name, questions):
    #insert if id not exists, else update
    existing_answer = db.session.get(Answer, applicant_id)
    if existing_answer:
        existing_answer.applicant_name = applicant_name
        existing_answer.questions = questions
    else:
        db.session.add(Answer(applicant_id=applicant_id, applicant_name=applicant_name, questions=questions,answers="{}"))
    db.session.commit()
    return 'saved successfully'


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
