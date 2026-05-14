from marshmallow import Schema, fields

class AnswerSchema(Schema):
    """Schema for the Answer model."""
    applicant_id = fields.Int(dump_only=True)
    applicant_name = fields.Str()
    questions = fields.Str()
