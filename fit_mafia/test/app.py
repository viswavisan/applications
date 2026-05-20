from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os

def create_app():
    app = Flask(__name__)
    CSRFProtect(app)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','test_secret_key')
    return app

app = create_app()
