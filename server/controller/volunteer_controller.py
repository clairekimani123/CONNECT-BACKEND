from flask import Blueprint, request, jsonify
from server.models import Volunteer, User
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity

volunteers_bp = Blueprint('volunteers', __name__, url_prefix='/volunteers')


@volunteers_bp.route('', methods=['GET'])
@jwt_required()
def get_volunteers():
    """Get all volunteers (Admin use)"""
    user = get_jwt_identity()
    volunteers = [v.to_dict() for v in Volunteer.query.all()]
    return jsonify(volunteers), 200


@volunteers_bp.route('/check', methods=['GET'])
def check_volunteer():
    """Check if a user is volunteering for an event"""
    user_id = request.args.get("user_id")
    event_id = request.args.get("event_id")

    exists = Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first()
    return jsonify({"volunteered": bool(exists)}), 200


@volunteers_bp.route('', methods=['POST'])
def create_volunteer():
    """
    Volunteer for a project.

    NOW REQUIRES the full signup details captured by VolunteerSignupForm —
    full_name and phone_number are required so a coordinator can actually
    reach out to and organise volunteers, not just see an email on file.
    availability, skills, and notes are optional context.
    """
    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    email = data.get("email")
    full_name = data.get("full_name")
    phone_number = data.get("phone_number")

    # NEW — required field validation matching the model's nullable=False
    if not user_id or not event_id:
        return jsonify({"error": "Missing user_id or event_id"}), 422
    if not email:
        return jsonify({"error": "Email is required"}), 422
    if not full_name or not full_name.strip():
        return jsonify({"error": "Full name is required"}), 422
    if not phone_number or not phone_number.strip():
        return jsonify({"error": "Phone number is required"}), 422

    if Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first():
        return jsonify({"error": "Already volunteering for this event"}), 409

    new_volunteer = Volunteer(
        user_id=user_id,
        event_id=event_id,
        email=email,
        full_name=full_name.strip(),
        phone_number=phone_number.strip(),
        availability=data.get("availability"),  # optional, can be None
        skills=data.get("skills"),               # optional, can be None
        notes=data.get("notes"),                 # optional, can be None
    )
    db.session.add(new_volunteer)
    db.session.commit()

    return jsonify(new_volunteer.to_dict()), 201


@volunteers_bp.route('', methods=['DELETE'])
def delete_volunteer():
    """Unvolunteer from an event — unchanged, no extra info needed to withdraw."""
    user_id = request.args.get("user_id")
    event_id = request.args.get("event_id")

    volunteer = Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first()

    if not volunteer:
        return jsonify({"error": "Not volunteering for this event"}), 404

    db.session.delete(volunteer)
    db.session.commit()

    return jsonify({"message": "Unvolunteered successfully"}), 200


@volunteers_bp.route('/project/<int:project_id>', methods=['GET'])
@jwt_required()
def get_volunteers_by_project(project_id):
    """
    NEW — admin/coordinator view of everyone who signed up for a specific
    project, with their full contact details for actually organising them.
    """
    volunteers = Volunteer.query.filter_by(event_id=project_id).all()
    return jsonify([v.to_dict() for v in volunteers]), 200