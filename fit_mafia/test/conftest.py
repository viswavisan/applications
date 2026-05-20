import time
import pytest
from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os

# --- APP SETUP ---

def create_test_app():
    app = Flask(__name__)
    CSRFProtect(app)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secure-random-string-for-testing')
    return app

# Make the app available globally for the tests
app = create_test_app()

# --- PYTEST HOOKS ---

def pytest_runtest_setup(item):
    item.start_time = time.time()

def pytest_runtest_teardown(item, nextitem):
    elapsed_time = time.time() - item.start_time
    print(f"{item.name} in {elapsed_time:.4f} seconds.")
