from flask import Blueprint, request, jsonify, make_response
from server.models import User
from server.config import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
            - password
            - fName
            - lName
          properties:
            email:
              type: string
            password:
              type: string
            fName:
              type: string
            lName:
              type: string
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields
      409:
        description: User already exists
    """
    data = request.get_json()
    print(data)

    email = data.get('email')
    password = data.get('password')
    first_name = data.get('fName')
    last_name = data.get('lName')

    # Validate required fields
    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    if not first_name or not last_name:
        return jsonify({'msg': 'First name and last name are required'}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'msg': 'User already exists'}), 409

    new_user = User(
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    new_user.password_hash = password

    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    # User does not exist
    if not user:
        return jsonify({'msg': 'Invalid credentials'}), 401

    # User registered via Google — has no password
    if not user._password_hash:
        return jsonify({'msg': 'This account uses Google sign-in. Please use the Google login button instead.'}), 401

    # Wrong password
    if not user.authenticate(password):
        return jsonify({'msg': 'Invalid credentials'}), 401

    access_token = create_access_token(identity={
        'id': user.id,
        'email': user.email,
        'role': user.role
    })

    return make_response(jsonify({
        "access_token": access_token,
        'id': user.id,
        'email': user.email,
        'role': user.role
    }), 200)

@auth_bp.route('/check_session', methods=['GET'])
@jwt_required()
def check_session():
    """
    Check current session (Requires JWT)
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Returns current user identity
    """
    current_user = get_jwt_identity()
    return jsonify(current_user), 200


@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    """
    Logout (Token invalidation depends on client-side)
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Logout message
    """
    return jsonify({"msg": "Token invalidation depends on client discarding token"}), 200


@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    """
    Firebase login with email
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
    responses:
      200:
        description: Firebase login successful, returns JWT token
      400:
        description: Missing email
    """
    data = request.get_json()
    print(data)

    # Fixed: was data.get('mail') — typo that caused 400 errors
    email = data.get('email')

    if not email:
        return jsonify({'msg': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()

    # If user doesn't exist, create one (Google sign-in, no password needed)
    if not user:
        user = User(
            email=email,
            first_name="Firebase",
            last_name="Login",
            role="user"
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity={
        'id': user.id,
        'email': user.email,
        'role': user.role
    })

    return make_response(jsonify({
        'access_token': access_token,
        'id': user.id,
        'email': user.email,
        'role': user.role
    }), 200)