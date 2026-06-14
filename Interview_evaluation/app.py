
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
import io
import sys
import traceback # Import traceback to get more detailed error info
from flask_smorest import Blueprint

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Blueprint('Evaluation', __name__,
                template_folder=template_dir,
                description="Operations for the Interview Evaluation application")
app.secret_key = 'your_secret_key'  # Needed for session management

# Path to the answers file
ANSWERS_FILE = 'answers.json'

# Python-related questions
QUESTIONS = [
    {
        "question": "Write a Python function to find the second largest number in a list.",
        "expected_output": "Example: `second_largest([10, 20, 4, 45, 99])` should return `45`."
    },
    {
        "question": "Write a Python program to reverse a string without using any built-in string reversal functions.",
        "expected_output": "Example: Reversing `'hello'` should result in `'olleh'`."
    },
    {
        "question": "Given a list of integers, write a function that returns a new list with all the duplicates removed.",
        "expected_output": "Example: For `[1, 2, 2, 3, 4, 4, 5]`, the output should be `[1, 2, 3, 4, 5]`."
    },
    {
        "question": "Write a Python function `is_palindrome` that checks if a given string is a palindrome.",
        "expected_output": "Example: `is_palindrome('racecar')` should return `True`."
    },
    {
        "question": "Write a Python program to count the frequency of each character in a given string and return it as a dictionary.",
        "expected_output": "Example: For `'hello'`, the output should be `{'h': 1, 'e': 1, 'l': 2, 'o': 1}`."
    },
    {
        "question": "Basic: Write code to split odd and even numbers from the range 1 to 10.",
        "expected_output": "Expected output: `([2, 4, 6, 8, 10], [1, 3, 5, 7, 9])`"
    }
]

@app.route('/')
def index():
    # Clear session to start fresh
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_interview():
    session['candidate_name'] = request.form['candidate_name']
    session['question_index'] = 0
    session['answers'] = {}
    return redirect(url_for('.interview'))

@app.route('/interview', methods=['GET', 'POST'])
def interview():
    # Protect against direct access
    if 'candidate_name' not in session:
        return redirect(url_for('.index'))

    if request.method == 'POST':
        # Store current answer before navigating
        answer = request.form.get('answer')
        question_index = session['question_index']
        answers = session.get('answers', {})
        answers[str(question_index)] = answer
        session['answers'] = answers

        # Handle navigation
        if 'back' in request.form:
            session['question_index'] -= 1
        elif 'next' in request.form:
            session['question_index'] += 1

        # Redirect to thank_you page if finished
        if session['question_index'] >= len(QUESTIONS):
            return redirect(url_for('.thank_you'))
        
        return redirect(url_for('.interview'))

    question_index = session.get('question_index', 0)
    
    # Ensure index is valid
    if not 0 <= question_index < len(QUESTIONS):
        return redirect(url_for('.thank_you'))

    question = QUESTIONS[question_index]
    
    # Get existing answer if available
    answers = session.get('answers', {})
    existing_answer = answers.get(str(question_index), '')

    progress = ((question_index + 1) / len(QUESTIONS)) * 100
    
    return render_template(
        'interview.html', 
        question=question, 
        existing_answer=existing_answer,
        progress=progress,
        is_first_question=(question_index == 0),
        is_last_question=(question_index == len(QUESTIONS) - 1),
        candidate_name=session.get('candidate_name'),
        question_number=question_index + 1,
        total_questions=len(QUESTIONS)
    )

@app.route('/run', methods=['POST'])
def run_code():
    """Executes Python code and returns the output."""
    code = request.json.get('code', '')
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    output = ''
    error = ''
    try:
        exec(code, {})
        output = redirected_output.getvalue()
    except Exception as e:
        output = redirected_output.getvalue()
        error = str(e) + "\n" + traceback.format_exc()
    finally:
        sys.stdout = old_stdout
    return jsonify({'output': output, 'error': error})

@app.route('/thank_you')
def thank_you():
    if 'candidate_name' not in session:
        return redirect(url_for('.index'))

    # Load existing submissions
    if os.path.exists(ANSWERS_FILE):
        with open(ANSWERS_FILE, 'r') as f:
            all_submissions = json.load(f)
    else:
        all_submissions = []

    # Format the final answers
    final_answers = {}
    raw_answers = session.get('answers', {})
    for i, q_data in enumerate(QUESTIONS):
        final_answers[q_data['question']] = raw_answers.get(str(i), "")

    # Create new submission object
    new_submission = {
        "candidate_name": session.get('candidate_name'),
        "submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "answers": final_answers
    }

    # Add new submission
    all_submissions.append(new_submission)

    # Save all submissions back to the file
    with open(ANSWERS_FILE, 'w') as f:
        json.dump(all_submissions, f, indent=4)
    
    # Clear the session
    session.clear()
    
    return render_template('thank_you.html')

@app.route('/review')
def review():
    if not os.path.exists(ANSWERS_FILE):
        return render_template('review.html', submissions=[])
        
    with open(ANSWERS_FILE, 'r') as f:
        try:
            all_submissions = json.load(f)
        except json.JSONDecodeError:
            all_submissions = []
    
    # Sort submissions by date, newest first
    all_submissions.sort(key=lambda x: x.get('submission_date', ''), reverse=True)

    return render_template('review.html', submissions=all_submissions)

if __name__ == '__main__':
    app.run(debug=True)
