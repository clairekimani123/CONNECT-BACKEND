# Import all blueprints for easy access
from .auth_controller import auth_bp
from .user_controller import users_bp
from .donation_controller import donations_bp
from .projects_controller import projects_bp
from .volunteer_controller import volunteers_bp

blueprints = [auth_bp, users_bp, donations_bp, projects_bp, volunteers_bp]









