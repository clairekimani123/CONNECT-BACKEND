import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
swagger = Swagger()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Reads from .env locally, from Render environment variables in production
DATABASE_URI = os.environ.get('DATABASE_URI', f"sqlite:///{os.path.join(BASE_DIR, '../instance/app.db')}")

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
