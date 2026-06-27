from flask import Blueprint, request, jsonify
from server.models import Donation, User, Project
from server.config import db
from server.services.mpesa_service import stk_push
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')


@donations_bp.route('', methods=['GET'])
def get_donations():
    donations = [donation.to_dict() for donation in Donation.query.all()]
    return jsonify(donations), 200


@donations_bp.route('', methods=['POST'])
def create_donation():
    """Create a non-mpesa donation (food, clothes, other).
    No payment confirmation step exists for these, so they're marked
    'completed' immediately — same as before this change."""
    data = request.get_json()
    user_id = data.get("user_id")
    project_id = data.get("project_id")

    try:
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({"error": "User not found"}), 404

        if project_id:
            project = Project.query.filter_by(id=project_id).first()
            if not project:
                return jsonify({"error": "Project not found"}), 404

        new_donation = Donation(
            type=data["type"],
            group=data["group"],
            details=data.get("description", ""),
            phone_number=data.get("phone"),
            amount=data.get("amount"),
            user_id=user_id,
            project_id=project_id,
            status='completed',  # non-mpesa donations have no pending state
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
    """
    Initiate an M-Pesa STK push.

    IMPORTANT — this no longer assumes the payment succeeded. The donation
    is created with status='pending'. It only becomes 'completed' (and
    therefore counts toward any dashboard totals) once mpesa_callback below
    receives Safaricom's actual confirmation.
    """
    current_user_id = get_jwt_identity()
    claims = get_jwt()

    data = request.get_json()
    phone = data.get('phone_number') or data.get('phone')
    amount = data.get('amount')
    group = data.get('group', 'General Donation')
    details = data.get('details', 'HopeConnect Donation')
    project_id = data.get('project_id')

    if not phone or not amount:
        return jsonify({'msg': 'Phone number and amount are required'}), 400

    if project_id:
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'msg': 'Project not found'}), 404

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
        checkout_request_id = result.get('CheckoutRequestID')

        donation = Donation(
            type='mpesa',
            group=group,
            details=details,
            phone_number=str(phone),
            amount=amount,
            user_id=int(current_user_id),
            project_id=project_id,
            status='pending',  # NEW — waiting for the callback to confirm
            checkout_request_id=checkout_request_id,  # NEW — so the callback can find this row
        )
        db.session.add(donation)
        db.session.commit()

        return jsonify({
            'msg': 'STK Push sent! Check your phone to complete payment.',
            'checkout_request_id': checkout_request_id,
            'donation_id': donation.id,
            'status': 'pending',  # NEW — frontend can show "awaiting confirmation"
        }), 200
    else:
        return jsonify({
            'msg': 'Payment initiation failed',
            'details': result
        }), 400


@donations_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """
    Handle M-Pesa payment callback from Safaricom.

    This is the ONLY place that should ever mark a donation as truly
    'completed'. Safaricom calls this endpoint automatically once the user
    enters their PIN (or cancels/times out) — it is not triggered by the
    frontend at all.
    """
    data = request.get_json()
    print("M-Pesa Callback received:", data)

    try:
        stk_callback = data['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']

        # NEW — find the donation row this callback belongs to
        donation = Donation.query.filter_by(
            checkout_request_id=checkout_request_id
        ).first()

        if not donation:
            print(f"No matching donation found for CheckoutRequestID {checkout_request_id}")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200

        if result_code == 0:
            # Payment genuinely succeeded
            items = stk_callback['CallbackMetadata']['Item']
            meta = {item['Name']: item.get('Value') for item in items}

            donation.status = 'completed'
            # Use the actual confirmed amount from Safaricom as a sanity check —
            # protects against a mismatch between what was requested and what
            # was actually paid.
            confirmed_amount = meta.get('Amount')
            if confirmed_amount:
                donation.amount = int(confirmed_amount)

            db.session.commit()
            print(f"Payment confirmed: KES {meta.get('Amount')} from {meta.get('PhoneNumber')} — donation {donation.id} marked completed")
        else:
            # User cancelled, wrong PIN, insufficient funds, timeout, etc.
            donation.status = 'failed'
            db.session.commit()
            print(f"Payment failed for donation {donation.id}: {stk_callback.get('ResultDesc')}")

    except Exception as e:
        print(f"Callback processing error: {e}")
        db.session.rollback()

    # Always return 200 to Safaricom regardless of what happened above —
    # this just acknowledges receipt of the callback, it's not a status
    # code for the donor.
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200


@donations_bp.route('/mpesa/status/<checkout_request_id>', methods=['GET'])
def get_donation_status(checkout_request_id):
    """
    NEW — lets the frontend poll for whether a pending donation has been
    confirmed yet, so the UI can show a real-time "payment confirmed!"
    state instead of assuming success immediately after the STK push.
    """
    donation = Donation.query.filter_by(checkout_request_id=checkout_request_id).first()
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    return jsonify({
        "status": donation.status,
        "amount": donation.amount,
        "donation_id": donation.id,
    }), 200


@donations_bp.route('/by-type/<donation_type>', methods=['GET'])
def get_donations_by_type(donation_type):
    donations = Donation.query.filter_by(type=donation_type).all()
    return jsonify([d.to_dict() for d in donations]), 200


@donations_bp.route('/by-group/<group_name>', methods=['GET'])
def get_donations_by_group(group_name):
    donations = Donation.query.filter_by(group=group_name).all()
    return jsonify([d.to_dict() for d in donations]), 200


@donations_bp.route('/by-project/<int:project_id>', methods=['GET'])
def get_donations_by_project(project_id):
    donations = Donation.query.filter_by(project_id=project_id).all()
    return jsonify([d.to_dict() for d in donations]), 200