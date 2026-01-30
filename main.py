# app.py
import os
import sys
from migrations import run_alembic_commands

from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Interview_evaluation')))
from Interview_evaluation.app import app

main_app = Flask(__name__)

@main_app.route("/run_alembic")
def run_alembic():
    run_alembic_commands.main()
    return "migration completed"

application = DispatcherMiddleware(main_app, {'/interview': app,})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)