from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Donation(db.Model, SerializerMixin):
    __tablename__ = 'donations'

    serialize_rules = ('-project.donations', '-user.donations')

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String, nullable=False)
    group = db.Column(db.String, nullable=False)
    details = db.Column(db.String)
    phone_number = db.Column(db.String(10))
    amount = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # NEW — links a donation to the project it's funding.
    # Nullable for now so existing rows (donated before this feature existed)
    # don't break; new donations should always set this.
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)

    user = db.relationship('User', back_populates='donations')
    project = db.relationship('Project', back_populates='donations')