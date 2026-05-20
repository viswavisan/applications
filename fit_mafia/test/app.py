from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['WTF_CSRF_ENABLED'] = False
    return app

app = create_app()
