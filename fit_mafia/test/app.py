from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    # You might need to initialize your database or other extensions here
    # For example:
    # from fit_mafia.db import db
    # db.init_app(app)
    
    return app

app = create_app()
