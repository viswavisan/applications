from flask import Blueprint, jsonify, request
from flask_smorest import Api

docs_blueprint = Blueprint('docs', __name__)

def configure_swagger(app):
    app.config["API_TITLE"] = "Interview Evaluation API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_ADD_DEFAULT_RESPONSE"] = False
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["OPENAPI_RAPIDOC_PATH"] = "/rapidoc"
    app.config["OPENAPI_RAPIDOC_URL"] = "https://unpkg.com/rapidoc/dist/rapidoc-min.js"
    app.register_blueprint(docs_blueprint)
    configure_error_handlers(app)
    return Api(app)

def configure_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(_):
        # Modern APIs typically return JSON instead of HTML
        # But we can smartly return JSON for API calls and HTML for browser visits
        
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({
                "error": "Not Found",
                "message": "The requested endpoint does not exist.",
                "status_code": 404
            }), 404
            
        # Optional: A more modern-looking HTML response with basic inline CSS
        rules = []
        for rule in app.url_map.iter_rules():
            # Exclude standard static routes and internal options
            if not str(rule).startswith("/static"):
                methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                rules.append(f"<tr><td><code>{rule.rule}</code></td><td><span class='badge'>{methods}</span></td></tr>")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 Not Found</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px auto; max-width: 800px; padding: 0 20px; color: #333; line-height: 1.6; }}
                h1 {{ color: #e53e3e; border-bottom: 2px solid #edf2f7; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
                th {{ background-color: #f7fafc; font-weight: 600; color: #4a5568; }}
                code {{ background-color: #edf2f7; padding: 4px 8px; border-radius: 4px; color: #2d3748; font-size: 0.9em; }}
                .badge {{ background-color: #ebf4ff; color: #3182ce; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
                .footer {{ margin-top: 40px; text-align: center; color: #718096; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>404 - Endpoint Not Found</h1>
            <p>The requested URL <code>{request.path}</code> was not found on this server.</p>
            <p>Here are the available endpoints you can try:</p>
            <table>
                <thead>
                    <tr>
                        <th>Endpoint</th>
                        <th>Allowed Methods</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(sorted(rules))}
                </tbody>
            </table>
            <div class="footer">Interview Evaluation API Service</div>
        </body>
        </html>
        """
        return html, 404

@docs_blueprint.route('/elements', methods=['GET'])
def elements_ui():
    """Serves the Stoplight Elements UI."""
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Stoplight Elements Documentation</title>
        <link rel="stylesheet" href="https://unpkg.com/@stoplight/elements/styles.min.css">
      </head>
      <body>
        <elements-api
          apiDescriptionUrl="/openapi.json"
          router="hash"
          layout="sidebar"
        />
        <script src="https://unpkg.com/@stoplight/elements/web-components.min.js"></script>
      </body>
    </html>
    """

@docs_blueprint.route('/scalar', methods=['GET'])
def scalar_ui():
    """Serves the Scalar API Reference UI."""
    return """
    <!doctype html>
    <html>
      <head>
        <title>Scalar API Reference</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <script
          id="api-reference"
          data-url="/openapi.json"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """
