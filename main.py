from flask import Flask
from flask_smorest import Api
import os
from datetime import timedelta
from Interview_evaluation.app import app as interview_blueprint
from fit_mafia.app import app as fit_mafia_blueprint
from migrations import run_alembic_commands

main_app = Flask(__name__)

main_app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
main_app.permanent_session_lifetime = timedelta(minutes=30)

main_app.config["API_TITLE"] = "Interview Evaluation API"
main_app.config["API_VERSION"] = "v1"
main_app.config["OPENAPI_VERSION"] = "3.0.2"
main_app.config["OPENAPI_URL_PREFIX"] = "/"
main_app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
main_app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(main_app)


@main_app.errorhandler(404)
def page_not_found(e):
    # Gather all registered endpoints
    rules = []
    for rule in main_app.url_map.iter_rules():
        # Filter out internal methods like HEAD/OPTIONS for cleaner output
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        rules.append(f"<li><b>{rule.rule}</b> [{methods}]</li>")

    html = (
        f"<h3>Page not found (404)</h3>"
        f"<p>The requested URL was not found. Here are the available endpoints:</p>"
        f"<ul>{''.join(sorted(rules))}</ul>"
        f"<p>{e}</p>"
    )
    return html, 404


@main_app.route("/run_alembic", methods=['GET'])
def run_alembic():
    run_alembic_commands.main()
    return "Migration completed", 200

@main_app.route("/health_check", methods=['GET'])
def healthcheck():
    return "Service active", 200


main_app.register_blueprint(interview_blueprint)
main_app.register_blueprint(fit_mafia_blueprint)

if __name__ == "__main__":
    main_app.run(host='0.0.0.0', port=5000)
    #workslocal http 5000 --name visan
    # sudo
    # firewall - cmd - -permanent - -add - service = http
    # sudo
    # firewall - cmd - -reload
