from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Expense(db.Model, SerializerMixin):
    __tablename__ = 'expenses'

    serialize_rules = ('-project.expenses',)

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    # What the money was spent on — keeps the dashboard breakdown meaningful.
    # e.g. "materials", "labor", "logistics", "permits", "other"
    category = db.Column(db.String, nullable=False)

    description = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

    project = db.relationship('Project', back_populates='expenses')

    def __repr__(self):
        return f'<Expense {self.category} - KES {self.amount} - Project {self.project_id}>'