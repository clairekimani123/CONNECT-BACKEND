from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Volunteer(db.Model, SerializerMixin):
    __tablename__ = 'volunteers'

    # FIXED — the previous rules only blocked the *direct* loop back
    # (volunteer.user.volunteer_signups) but didn't stop other relationship
    # chains from looping, e.g.:
    #   Volunteer -> user -> donations -> project -> volunteers -> user -> ...
    #
    # Rather than trying to enumerate every possible loop combination (fragile,
    # and easy to miss one — which is exactly what happened here), we cut off
    # ALL nested relationships on `user` and `project` beyond their own scalar
    # fields. A volunteer record doesn't need its user's full donation history
    # or its project's full volunteer list nested inside it anyway — if you
    # need that, fetch it separately with its own endpoint.
    serialize_rules = (
        '-project.volunteers',
        '-project.donations',
        '-project.expenses',
        '-user.volunteer_signups',
        '-user.donations',
        '-user._password_hash',
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    email = db.Column(db.String, nullable=False)

    full_name = db.Column(db.String, nullable=True, server_default="Not provided")
    phone_number = db.Column(db.String(15), nullable=True, server_default="Not provided")

    availability = db.Column(db.String, nullable=True)
    skills = db.Column(db.String, nullable=True)
    notes = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    project = db.relationship('Project', back_populates='volunteers')
    user = db.relationship('User', back_populates='volunteer_signups')

    def __repr__(self):
        return f'<Volunteer ID: {self.id}, Name: {self.full_name}, Event ID: {self.event_id}>'