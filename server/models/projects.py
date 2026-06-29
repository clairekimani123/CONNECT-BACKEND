from server.config import db
from datetime import datetime, date
from sqlalchemy_serializer import SerializerMixin

class Project(db.Model, SerializerMixin):
    __tablename__ = 'projects'

    # FIXED — cut off nested relationships on volunteers/donations/expenses
    # entirely, not just the single direct back-reference. A Project's
    # volunteer list doesn't need each volunteer's full user object with
    # THEIR full donation history nested inside — that's the chain that
    # caused the recursion.
    serialize_rules = (
        '-volunteers.project',
        '-volunteers.user.donations',
        '-volunteers.user.volunteer_signups',
        '-donations.project',
        '-donations.user.donations',
        '-donations.user.volunteer_signups',
        '-expenses.project',
    )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=False)

    target_amount = db.Column(db.Integer, nullable=True, default=0)

    volunteers = db.relationship('Volunteer', back_populates='project', lazy=True)
    donations = db.relationship('Donation', back_populates='project', lazy=True)
    expenses = db.relationship('Expense', back_populates='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.type} - ID: {self.id}>'