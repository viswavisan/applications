import datetime
import os

from flask import flash, redirect, render_template, request, session, url_for, jsonify
from flask_smorest import Blueprint

from fit_mafia import app_controller
from fit_mafia.constants import HOME_PAGE, PUBLIC_PAGE, LOGIN_PAGE, PUBLIC_TEMPLATE, RECEIPT_TEMPLATE
from fit_mafia.schemas import MemberSchema,LoginRequestSchema

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))


app = Blueprint('fit_mafia', __name__, template_folder=template_dir,
                description="Operations for the Fit Mafia application")

@app.before_request
def require_auth():
    """Check authentication before every request in this Blueprint except public endpoints."""
    public_endpoints = [PUBLIC_PAGE, LOGIN_PAGE]

    if request.endpoint and (request.endpoint.startswith('static') or request.endpoint in public_endpoints):
        return None

    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for(PUBLIC_PAGE))

    now = datetime.datetime.now()
    if app_controller.handle_session_timeout(now):
        return redirect(url_for(PUBLIC_PAGE))

    session.permanent = True
    if 'session_id' not in session:
        app_controller.create_db_session(session.get('username', 'Admin'))

    session['last_active'] = now.isoformat()
    return None

@app.route('/', methods=['GET'])
def public_page():
    """Renders the public-facing page, or redirects to home if logged in."""
    if session.get('logged_in'):
        return redirect(url_for(HOME_PAGE))
    return render_template(PUBLIC_TEMPLATE)


@app.route('/home', methods=['GET'])
def home():
    response=app_controller.home()
    if response['status']=='success':
        template_data=response['template_data']
        return render_template('home.html', **template_data)
    else:
        flash(response['message'], "error")
        return render_template(PUBLIC_TEMPLATE, error=response['message'])

@app.route('/logout', methods=['GET'])
def logout():
    app_controller.logout()
    flash("You have been logged out.", "info")
    return redirect(url_for(PUBLIC_PAGE))


@app.route('/print_receipt/<transaction_id>', methods=['GET'])
def print_receipt(transaction_id):
    response=app_controller.print_receipt(transaction_id)
    if response['status']=='success':
        return render_template(RECEIPT_TEMPLATE, **response['template_data'])
    else:
        return redirect(url_for(HOME_PAGE))


@app.route('/api/member/<mobile_number>', methods=['GET'])
@app.response(200, MemberSchema)
def get_member(mobile_number):
    response=app_controller.get_member(mobile_number)
    if response['status']=='success':
        return response['message']
    else:
        return jsonify({response['status']: response['message']}), response['code']


@app.route('/login', methods=['POST'])
@app.arguments(LoginRequestSchema, location="form")
def login(args):
    """User Login"""
    try:
        username = args["username"]
        password = args["password"]
        response=app_controller.login(username,password)
        if response['status']=='success':
            return redirect(url_for(HOME_PAGE))
        else:
            flash(response['message'], "error")
            return render_template(PUBLIC_TEMPLATE, error=response['message'])
    except Exception as e:
        print (e)

@app.route('/register_transaction', methods=['POST'])
def register_transaction():
    response=app_controller.register_transaction()
    if response['status']=="success":
        return redirect(url_for(HOME_PAGE))
    else:
        flash(response['message'], "error")
        return redirect(url_for(HOME_PAGE))

@app.route('/register_member', methods=['POST'])
def register_member():
    response=app_controller.register_member()
    if response['status']=='success':
        flash(response['message'], "success")
    else:
        flash("Member registered successfully!", "error")
    return redirect(url_for(HOME_PAGE))

@app.route('/update_vitals', methods=['POST'])
def update_vitals():
    response=app_controller.update_vitals()
    return jsonify({response['status']: response['message']}), response['code']

@app.route('/renew_subscription', methods=['POST'])
def renew_subscription():
    response=app_controller.renew_subscription()
    return jsonify({response['status']: response['message']}), response['code']
