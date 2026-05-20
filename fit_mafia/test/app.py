from flask import Flask

def create_app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    test_app.config['WTF_CSRF_ENABLED'] = False
    return test_app

app = create_app()
