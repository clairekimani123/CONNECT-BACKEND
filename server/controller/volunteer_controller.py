from flask import Blueprint, request, jsonify
from server.models import Volunteer, User
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity

volunteers_bp = Blueprint('volunteers', __name__, url_prefix='/volunteers')


@volunteers_bp.route('', methods=['GET'])
@jwt_required()
def get_volunteers():
    """
    Get all volunteers (Admin use)
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: List of volunteers
        examples:
          application/json: [{"id": 1, "user_id": 2, "event_id": 3}]
    """
    user = get_jwt_identity()
    volunteers = [v.to_dict() for v in Volunteer.query.all()]
    return jsonify(volunteers), 200


@volunteers_bp.route('/check', methods=['GET'])
def check_volunteer():
    """
    Check if a user is volunteering for an event
    ---
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: ID of the user
      - name: event_id
        in: query
        type: integer
        required: true
        description: ID of the event
    responses:
      200:
        description: Volunteer status
        examples:
          application/json: {"volunteered": true}
    """
    user_id = request.args.get("user_id")
    event_id = request.args.get("event_id")

    exists = Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first()
    return jsonify({"volunteered": bool(exists)}), 200


@volunteers_bp.route('', methods=['POST'])
def create_volunteer():
    """
    Volunteer for an event
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - user_id
            - event_id
            - email
          properties:
            user_id:
              type: integer
            event_id:
              type: integer
            email:
              type: string
    responses:
      201:
        description: Volunteer created
      409:
        description: Already volunteering
      422:
        description: Missing user_id or event_id
    """
    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    email = data.get("email")

    if not user_id or not event_id:
        return jsonify({"error": "Missing user_id or event_id"}), 422

    if Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first():
        return jsonify({"error": "Already volunteering for this event"}), 409

    new_volunteer = Volunteer(user_id=user_id, event_id=event_id, email=email)
    db.session.add(new_volunteer)
    db.session.commit()

    return jsonify(new_volunteer.to_dict()), 201


@volunteers_bp.route('', methods=['DELETE'])
def delete_volunteer():
    """
    Unvolunteer from an event
    ---
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: ID of the user
      - name: event_id
        in: query
        type: integer
        required: true
        description: ID of the event
    responses:
      200:
        description: Unvolunteered successfully
      404:
        description: Not volunteering for this event
    """
    user_id = request.args.get("user_id")
    event_id = request.args.get("event_id")

    volunteer = Volunteer.query.filter_by(user_id=user_id, event_id=event_id).first()

    if not volunteer:
        return jsonify({"error": "Not volunteering for this event"}), 404

    db.session.delete(volunteer)
    db.session.commit()

    return jsonify({"message": "Unvolunteered successfully"}), 200
