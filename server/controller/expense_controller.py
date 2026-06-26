from flask import Blueprint, request, jsonify
from server.models import Expense, Project, User
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

ALLOWED_CATEGORIES = ['materials', 'labor', 'logistics', 'permits', 'other']


def _require_admin():
    """
    Shared admin check, matching the role field already on your User model.
    Returns None if the caller is an admin, or an (response, status) tuple to
    return immediately if they are not.
    """
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    return None


@expenses_bp.route('', methods=['GET'])
def get_expenses():
    """Get all expenses (public — supports the transparency dashboard)."""
    expenses = [expense.to_dict() for expense in Expense.query.all()]
    return jsonify(expenses), 200


@expenses_bp.route('/project/<int:project_id>', methods=['GET'])
def get_expenses_by_project(project_id):
    """Get all expenses for a single project."""
    expenses = Expense.query.filter_by(project_id=project_id).all()
    return jsonify([e.to_dict() for e in expenses]), 200


@expenses_bp.route('', methods=['POST'])
@jwt_required()
def create_expense():
    """
    Log a new expense against a project. Admin only — anyone able to post
    fake expenses would undermine the entire point of the transparency
    dashboard, so this is locked down the same way project creation now is.
    """
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing expense data"}), 422

    try:
        project = Project.query.filter_by(id=data["project_id"]).first()
        if not project:
            return jsonify({"error": "Project not found"}), 404

        category = data.get("category", "other")
        if category not in ALLOWED_CATEGORIES:
            return jsonify({"error": f"Category must be one of {ALLOWED_CATEGORIES}"}), 422

        new_expense = Expense(
            project_id=data["project_id"],
            category=category,
            description=data["description"],
            amount=int(data["amount"]),
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify(new_expense.to_dict()), 201

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 422
    except ValueError:
        return jsonify({"error": "Amount must be a number"}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422


@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense. Admin only."""
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    expense = Expense.query.filter_by(id=expense_id).first()
    if not expense:
        return jsonify({"error": "Expense not found"}), 404

    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422