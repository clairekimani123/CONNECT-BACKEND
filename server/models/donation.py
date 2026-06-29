from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Donation(db.Model, SerializerMixin):
    __tablename__ = 'donations'

    # FIXED — same recursion issue as Volunteer. Cut off project's and
    # user's nested relationships entirely rather than just the single
    # direct loop-back path, since a donation can be reached through
    # multiple different relationship chains (directly, or via a
    # volunteer -> user -> donations path, etc.)
    serialize_rules = (
        '-project.donations',
        '-project.volunteers',
        '-project.expenses',
        '-user.donations',
        '-user.volunteer_signups',
        '-user._password_hash',
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String, nullable=False)
    group = db.Column(db.String, nullable=False)
    details = db.Column(db.String)
    phone_number = db.Column(db.String(10))
    amount = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)

    status = db.Column(db.String, nullable=False, default='completed')
    checkout_request_id = db.Column(db.String, nullable=True, index=True)

    user = db.relationship('User', back_populates='donations')
    project = db.relationship('Project', back_populates='donations')