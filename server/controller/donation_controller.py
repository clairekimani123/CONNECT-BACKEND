from flask import Blueprint, request, jsonify
from server.models import Donation, User
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')


@donations_bp.route('', methods=['GET'])
def get_donations():
    """
    Get all donations
    ---
    responses:
      200:
        description: List of all donations
        examples:
          application/json: [{"id": 1, "type": "Food", "group": "Community", "amount": 50}]
    """
    donations = [donation.to_dict() for donation in Donation.query.all()]
    return jsonify(donations), 200


@donations_bp.route('', methods=['POST'])
def create_donation():
    """
    Create a new donation (Requires JWT)
    ---
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - type
            - group
            - phone_number
            - amount
          properties:
            type:
              type: string
            group:
              type: string
            details:
              type: string
            phone_number:
              type: string
            amount:
              type: number
    responses:
      201:
        description: Donation created successfully
      404:
        description: User not found
      422:
        description: Missing or invalid data
    """
    
    data = request.get_json()
    user_id = data.get("user_id")
    try:
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found"}), 404

        new_donation = Donation(
            type=data["type"],
            group=data["group"],
            details=data.get("description", ""),
            phone_number=data.get("phone"),
            amount=data.get("amount"),
            user_id=user_id
        )
        
        db.session.add(new_donation)
        db.session.commit()
        
        return jsonify(new_donation.to_dict()), 201
    
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422


@donations_bp.route('/by-type/<donation_type>', methods=['GET'])
def get_donations_by_type(donation_type):
    """
    Get donations by type
    ---
    parameters:
      - name: donation_type
        in: path
        type: string
        required: true
        description: Type of donation to filter by
    responses:
      200:
        description: List of donations matching the type
    """
    donations = Donation.query.filter_by(type=donation_type).all()
    return jsonify([donation.to_dict() for donation in donations]), 200


@donations_bp.route('/by-group/<group_name>', methods=['GET'])
def get_donations_by_group(group_name):
    """
    Get donations by group
    ---
    parameters:
      - name: group_name
        in: path
        type: string
        required: true
        description: Group name to filter donations
    responses:
      200:
        description: List of donations matching the group
    """
    donations = Donation.query.filter_by(group=group_name).all()
    return jsonify([donation.to_dict() for donation in donations]), 200
