from flask import Blueprint, request, jsonify
from server.models import Project, Donation, Expense
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime


projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


def _require_admin():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    return None


@projects_bp.route('', methods=['GET'])
def get_projects():
    projects = [project.to_dict() for project in Project.query.all()]
    return jsonify(projects), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
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


def _calculate_project_stats(project):
    """
    Shared helper — computes the same raised/spent/target numbers used by
    both the single-project dashboard and the new org-wide breakdown below,
    so the two endpoints can never drift out of sync with each other.
    """
    donations = Donation.query.filter_by(
        project_id=project.id,
        status='completed',
    ).all()
    expenses = Expense.query.filter_by(project_id=project.id).all()

    raised = sum(d.amount or 0 for d in donations)
    spent = sum(e.amount or 0 for e in expenses)
    target = project.target_amount or 0
    percent_funded = round((raised / target) * 100, 1) if target > 0 else 0
    percent_funded = min(percent_funded, 100)

    return {
        "raised": raised,
        "spent": spent,
        "remaining": raised - spent,
        "target": target,
        "percent_funded": percent_funded,
        "donor_count": len(donations),
    }


@projects_bp.route('/<int:project_id>/dashboard', methods=['GET'])
def get_project_dashboard(project_id):
    """Transparency dashboard for a single project."""
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    stats = _calculate_project_stats(project)  # reuses the shared helper now

    expenses = Expense.query.filter_by(project_id=project_id).all()
    breakdown = {}
    for e in expenses:
        breakdown[e.category] = breakdown.get(e.category, 0) + e.amount

    pending_count = Donation.query.filter_by(
        project_id=project_id,
        status='pending',
    ).count()

    return jsonify({
        "project_id": project_id,
        "project_type": project.type,
        **stats,
        "pending_donations": pending_count,
        "expense_breakdown": breakdown,
    }), 200


@projects_bp.route('/dashboard/overview', methods=['GET'])
def get_overview_dashboard():
    """
    Org-wide totals AND a per-project breakdown, so a donor can see at a
    glance — right on the homepage, before clicking into any single
    project — exactly how much each individual project has raised.
    """
    all_donations = Donation.query.filter_by(status='completed').all()
    all_expenses = Expense.query.all()

    total_raised = sum(d.amount or 0 for d in all_donations)
    total_spent = sum(e.amount or 0 for e in all_expenses)

    overall_breakdown = {}
    for e in all_expenses:
        overall_breakdown[e.category] = overall_breakdown.get(e.category, 0) + e.amount

    # NEW — per-project stats, reusing the exact same calculation as the
    # single-project dashboard endpoint above
    all_projects = Project.query.all()
    project_breakdown = []
    for project in all_projects:
        stats = _calculate_project_stats(project)
        project_breakdown.append({
            "project_id": project.id,
            "project_type": project.type,
            "image_url": project.image_url,
            **stats,
        })

    # Sort highest-raised first — donors naturally want to see the most
    # active/successful projects first
    project_breakdown.sort(key=lambda p: p["raised"], reverse=True)

    return jsonify({
        "total_raised": total_raised,
        "total_spent": total_spent,
        "total_remaining": total_raised - total_spent,
        "donor_count": len(all_donations),
        "project_count": len(all_projects),
        "expense_breakdown": overall_breakdown,
        "projects": project_breakdown,  # NEW
    }), 200