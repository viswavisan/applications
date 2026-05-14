from flask import Flask
from flask_smorest import Api
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

from Interview_evaluation.app import app as interview_blueprint
from fit_mafia.app import app as fit_mafia_blueprint
from health_check import app as health_blueprint

main_app = Flask(__name__)

main_app.config["API_TITLE"] = "Interview Evaluation API"
main_app.config["API_VERSION"] = "v1"
main_app.config["OPENAPI_VERSION"] = "3.0.2"
main_app.config["OPENAPI_ADD_DEFAULT_RESPONSE"] = False
main_app.config["OPENAPI_URL_PREFIX"] = "/"
main_app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
main_app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


main_app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
main_app.permanent_session_lifetime = timedelta(minutes=30)

@main_app.errorhandler(404)
def page_not_found(e):
    rules = []
    for rule in main_app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        rules.append(f"<li><b>{rule.rule}</b> [{methods}]</li>")

    html = (
        f"<h3>Page not found (404)</h3>"
        f"<p>The requested URL was not found. Here are the available endpoints:</p>"
        f"<ul>{''.join(sorted(rules))}</ul>"
        f"<p>{e}</p>"
    )
    return html, 404

# Register all blueprints
api = Api(main_app)
api.register_blueprint(health_blueprint)
api.register_blueprint(fit_mafia_blueprint)
api.register_blueprint(interview_blueprint)


if __name__ == "__main__":
    main_app.run(host='127.0.0.1', port=5000)
    #workslocal http 5000 --name visan
    # sudo
    # firewall - cmd - -permanent - -add - service = http
    # sudo
    # firewall - cmd - -reload
