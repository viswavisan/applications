from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields

class HealthStatusSchema(Schema):
    """Schema for a successful health check response."""
    status = fields.Str(required=True, description="Indicates the operational status of the service.")

class HealthErrorSchema(Schema):
    """Schema for a generic error response."""
    code = fields.Int(required=True, description="HTTP status code.")
    message = fields.Str(required=True, description="A description of the error.")


app = Blueprint("Health", "health", description="Health check for the service")

@app.route("/health_check")
class HealthCheck(MethodView):
    @app.response(200, HealthStatusSchema)
    @app.alt_response(503, schema=HealthErrorSchema, description="Service Unavailable")
    def get(self):
        return {"status": "active"}
