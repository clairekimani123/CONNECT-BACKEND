from server.config import db, bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    # FIXED — same recursion-prevention pattern. Cut nested relationships
    # on each donation/volunteer_signup's own user/project, not just the
    # single direct back-reference.
    serialize_rules = (
        "-donations.user",
        "-donations.project.volunteers",
        "-donations.project.donations",
        "-donations.project.expenses",
        "-volunteer_signups.user",
        "-volunteer_signups.project.volunteers",
        "-volunteer_signups.project.donations",
        "-volunteer_signups.project.expenses",
        "-_password_hash",
    )

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)
    role = db.Column(db.String, default="user")

    donations = db.relationship('Donation', back_populates='user', lazy=True)
    volunteer_signups = db.relationship('Volunteer', back_populates='user', lazy=True)

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))

    def __repr__(self):
        return f'User {self.email}, ID: {self.id}'