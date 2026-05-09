from flask import Blueprint, request, jsonify
from server.models import Donation, User
from server.config import db
from server.services.mpesa_service import stk_push
from flask_jwt_extended import jwt_required, get_jwt_identity

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')


@donations_bp.route('', methods=['GET'])
def get_donations():
    donations = [donation.to_dict() for donation in Donation.query.all()]
    return jsonify(donations), 200


@donations_bp.route('', methods=['POST'])
def create_donation():
    """Create a non-mpesa donation (food, clothes, other)"""
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


@donations_bp.route('/mpesa', methods=['POST'])
@jwt_required()
def mpesa_donate():
    """Initiate M-Pesa STK Push donation"""
    current_user = get_jwt_identity()
    data = request.get_json()

    phone = data.get('phone_number') or data.get('phone')
    amount = data.get('amount')
    group = data.get('group', 'General Donation')
    details = data.get('details', 'HopeConnect Donation')

    if not phone or not amount:
        return jsonify({'msg': 'Phone number and amount are required'}), 400

    try:
        amount = int(amount)
        if amount < 1:
            return jsonify({'msg': 'Amount must be at least KES 1'}), 400
    except ValueError:
        return jsonify({'msg': 'Invalid amount'}), 400

    result = stk_push(
        phone_number=phone,
        amount=amount,
        account_reference="HopeConnect",
        description=details
    )

    if 'error' in result:
        return jsonify({'msg': 'Payment initiation failed', 'error': result['error']}), 500

    if result.get('ResponseCode') == '0':
        donation = Donation(
            type='mpesa',
            group=group,
            details=details,
            phone_number=str(phone),
            amount=amount,
            user_id=current_user['id']
        )
        db.session.add(donation)
        db.session.commit()

        return jsonify({
            'msg': 'STK Push sent! Check your phone to complete payment.',
            'checkout_request_id': result.get('CheckoutRequestID'),
            'donation_id': donation.id
        }), 200
    else:
        return jsonify({
            'msg': 'Payment initiation failed',
            'details': result
        }), 400


@donations_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa payment callback from Safaricom"""
    data = request.get_json()
    print("M-Pesa Callback received:", data)

    try:
        stk_callback = data['Body']['stkCallback']
        result_code = stk_callback['ResultCode']

        if result_code == 0:
            items = stk_callback['CallbackMetadata']['Item']
            meta = {item['Name']: item.get('Value') for item in items}
            print(f"Payment successful: KES {meta.get('Amount')} from {meta.get('PhoneNumber')}")
        else:
            print(f"Payment failed: {stk_callback.get('ResultDesc')}")

    except Exception as e:
        print(f"Callback processing error: {e}")

    return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200


@donations_bp.route('/by-type/<donation_type>', methods=['GET'])
def get_donations_by_type(donation_type):
    donations = Donation.query.filter_by(type=donation_type).all()
    return jsonify([d.to_dict() for d in donations]), 200


@donations_bp.route('/by-group/<group_name>', methods=['GET'])
def get_donations_by_group(group_name):
    donations = Donation.query.filter_by(group=group_name).all()
    return jsonify([d.to_dict() for d in donations]), 200
