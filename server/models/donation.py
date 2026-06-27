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
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)

    # NEW — tracks whether real money has actually moved.
    # 'pending'   = STK push sent, waiting for the user to enter their PIN
    # 'completed' = Safaricom confirmed payment succeeded — only these count
    #               toward the transparency dashboard totals
    # 'failed'    = user cancelled, wrong PIN, insufficient funds, timeout, etc.
    # Non-mpesa donations (food/clothes/other) are created as 'completed'
    # immediately since there's no payment confirmation step for those.
    status = db.Column(db.String, nullable=False, default='completed')

    # NEW — Safaricom's CheckoutRequestID, the only reliable way to match
    # an incoming callback back to the donation row that triggered it.
    checkout_request_id = db.Column(db.String, nullable=True, index=True)

    user = db.relationship('User', back_populates='donations')
    project = db.relationship('Project', back_populates='donations')