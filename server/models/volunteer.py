from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Volunteer(db.Model, SerializerMixin):
    __tablename__ = 'volunteers'

    serialize_rules = (
        '-project.volunteers',
        '-user.volunteer_signups',
        '-user.password',
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    email = db.Column(db.String, nullable=False)

    # Fields a real coordinator needs to actually organise volunteers.
    #
    # IMPORTANT — made safe for migrating an existing table with rows
    # already in it: nullable=True with a server_default. Without a
    # server_default, Postgres/SQLite would reject the migration outright
    # because existing rows (created before these columns existed) have
    # no value to put here. New signups will always provide a real value
    # through the form, so this is just a safety net for old rows.
    full_name = db.Column(db.String, nullable=True, server_default="Not provided")
    phone_number = db.Column(db.String(15), nullable=True, server_default="Not provided")

    availability = db.Column(db.String, nullable=True)  # e.g. "weekends", "weekdays", "flexible"
    skills = db.Column(db.String, nullable=True)         # free text, e.g. "first aid, driving, teaching"
    notes = db.Column(db.String, nullable=True)          # anything else the volunteer wants to mention

    created_at = db.Column(db.DateTime, default=datetime.now)

    project = db.relationship('Project', back_populates='volunteers')
    user = db.relationship('User', back_populates='volunteer_signups')

    def __repr__(self):
        return f'<Volunteer ID: {self.id}, Name: {self.full_name}, Event ID: {self.event_id}>'