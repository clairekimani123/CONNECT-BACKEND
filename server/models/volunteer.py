from server.config import db
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

    project = db.relationship('Project', back_populates='volunteers')
    user = db.relationship('User', back_populates='volunteer_signups')

    def __repr__(self):
        return f'<Volunteer ID: {self.id}, Name: {self.first_name} {self.last_name}, Event ID: {self.event_id}>'
