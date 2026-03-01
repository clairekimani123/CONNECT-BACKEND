from server.config import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

class Donation(db.Model, SerializerMixin):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    type = db.Column(db.String,nullable=False)
    group = db.Column(db.String, nullable=False)
    details = db.Column(db.String)
    phone_number = db.Column(db.String(10))
    amount = db.Column(db.Integer)
    user_id =db.Column(db.Integer, db.ForeignKey("users.id"))
    
    user = db.relationship('User', back_populates='donations')
