from flask import Blueprint, request, jsonify
from server.models import Project, Donation, Expense
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime


projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


def _require_admin():
    """Shared admin check — see expense_controller.py for the same helper."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    return None


@projects_bp.route('', methods=['GET'])
def get_projects():
    """
    Get all projects
    ---
    responses:
      200:
        description: List of all projects
    """
    projects = [project.to_dict() for project in Project.query.all()]
    return jsonify(projects), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """
    Create a new project. Admin only.
    ---
    security:
      - Bearer: []
    consumes:
      - application/json
    responses:
      201:
        description: Project created successfully
      403:
        description: Admin access required
      422:
        description: Missing or invalid project data
    """
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing project data"}), 422

    try:
        date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()

        new_project = Project(
            type=data["type"],
            description=data["description"],
            date=date_obj,
            image_url=data["image_url"],
            target_amount=data.get("target_amount", 0),
        )

        db.session.add(new_project)
        db.session.commit()

        return jsonify(new_project.to_dict()), 201

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """
    Delete a project by ID. Admin only.
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: Project deleted successfully
      403:
        description: Admin access required
      404:
        description: Project not found
    """
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422


@projects_bp.route('/<int:project_id>/dashboard', methods=['GET'])
def get_project_dashboard(project_id):
    """
    Transparency dashboard data for a single project — public, no auth
    required, since the entire point is for anyone to see exactly where
    money raised for this project has gone.

    Returns:
      raised            total of all donations linked to this project
      spent             total of all expenses linked to this project
      remaining         raised - spent
      target            the project's fundraising goal (0 if not set)
      percent_funded    raised / target * 100, capped at 100, 0 if no target
      expense_breakdown spending grouped by category, for a pie/bar chart
    """
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    donations = Donation.query.filter_by(project_id=project_id).all()
    expenses = Expense.query.filter_by(project_id=project_id).all()

    raised = sum(d.amount or 0 for d in donations)
    spent = sum(e.amount or 0 for e in expenses)
    target = project.target_amount or 0

    percent_funded = round((raised / target) * 100, 1) if target > 0 else 0
    percent_funded = min(percent_funded, 100)

    breakdown = {}
    for e in expenses:
        breakdown[e.category] = breakdown.get(e.category, 0) + e.amount

    return jsonify({
        "project_id": project_id,
        "project_type": project.type,
        "raised": raised,
        "spent": spent,
        "remaining": raised - spent,
        "target": target,
        "percent_funded": percent_funded,
        "donor_count": len(donations),
        "expense_breakdown": breakdown,
    }), 200


@projects_bp.route('/dashboard/overview', methods=['GET'])
def get_overview_dashboard():
    """
    Organization-wide transparency totals across ALL projects.
    Powers a top-level "our impact" summary, separate from the
    per-project breakdown above.
    """
    all_donations = Donation.query.all()
    all_expenses = Expense.query.all()

    total_raised = sum(d.amount or 0 for d in all_donations)
    total_spent = sum(e.amount or 0 for e in all_expenses)

    breakdown = {}
    for e in all_expenses:
        breakdown[e.category] = breakdown.get(e.category, 0) + e.amount

    return jsonify({
        "total_raised": total_raised,
        "total_spent": total_spent,
        "total_remaining": total_raised - total_spent,
        "donor_count": len(all_donations),
        "project_count": Project.query.count(),
        "expense_breakdown": breakdown,
    }), 200