from server.config import db
from datetime import datetime, date
from sqlalchemy_serializer import SerializerMixin

class Project(db.Model, SerializerMixin):
    __tablename__ = 'projects'

    serialize_rules = (
        '-volunteers.project',
        '-donations.project',
        '-expenses.project',
    )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=False)

    # NEW — the fundraising goal for this project.
    # Nullable so existing projects don't break; defaults to 0 if not set,
    # the dashboard treats 0 as "no target set" and just shows raised/spent.
    target_amount = db.Column(db.Integer, nullable=True, default=0)

    volunteers = db.relationship('Volunteer', back_populates='project', lazy=True)

    # NEW relationships — required for the transparency dashboard aggregation
    donations = db.relationship('Donation', back_populates='project', lazy=True)
    expenses = db.relationship('Expense', back_populates='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.type} - ID: {self.id}>'