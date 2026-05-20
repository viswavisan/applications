import time
from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os

# --- APP SETUP ---

def create_test_app():
    test_app = Flask(__name__)
    CSRFProtect(test_app)
    test_app.config['TESTING'] = True
    test_app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
    return test_app

# Make the app available globally for the tests
app = create_test_app()

# --- PYTEST HOOKS ---

def pytest_runtest_setup(item):
    item.start_time = time.time()

def pytest_runtest_teardown(item):
    elapsed_time = time.time() - item.start_time
    print(f"{item.name} in {elapsed_time:.4f} seconds.")
