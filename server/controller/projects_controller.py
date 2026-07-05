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


# ── NEW — PATCH /projects/<id> ─────────────────────────────────────────────
# Think of this like a document editor — the POST endpoint above creates a
# brand new document from scratch, while this PATCH endpoint lets you open
# an existing document and change only the fields you want, leaving
# everything else exactly as it was.
#
# This is a permanent, useful endpoint — not just for the one-time seed.
# Your admin panel needs this so coordinators can correct a typo in a
# project description or update a fundraising target without deleting and
# recreating the entire project (which would wipe its donation history).

@projects_bp.route('/<int:project_id>', methods=['PATCH'])
@jwt_required()
def update_project(project_id):
    """
    Edit an existing project. Admin only.
    Only the fields included in the request body are updated — anything
    not mentioned is left exactly as it was. This is the PATCH pattern:
    partial update, not a full replacement.
    """
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 422

    try:
        # Only update a field if it was actually sent in the request.
        # This is the key difference between PATCH and PUT — PUT requires
        # you to send the entire object every time, PATCH only requires
        # the fields you actually want to change.
        if "type" in data:
            project.type = data["type"]
        if "description" in data:
            project.description = data["description"]
        if "image_url" in data:
            project.image_url = data["image_url"]
        if "target_amount" in data:
            project.target_amount = int(data["target_amount"])
        if "date" in data:
            project.date = datetime.strptime(data["date"], "%Y-%m-%d").date()

        db.session.commit()
        return jsonify(project.to_dict()), 200

    except ValueError as e:
        return jsonify({"error": f"Invalid value: {str(e)}"}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 422


# ── ONE-TIME SEED ROUTE ────────────────────────────────────────────────────
# Think of this like a master key that opens every room in the building at
# once — useful right now to do a bulk repaint, but you hand it back and
# destroy it the moment the work is done. It has no place on a keychain
# that staff carry every day.
#
# HOW TO USE:
#   1. Deploy this file
#   2. Call GET /projects/seed-real-data from Postman with your admin JWT
#   3. Confirm all 6 rows return "updated: true"
#   4. Delete this entire route block and redeploy
#
# DO NOT leave this route in production — it runs unconditionally on any
# admin call, meaning a mistaken second call would overwrite any edits
# made through the admin panel after the first run.

@projects_bp.route('/seed-real-data', methods=['GET'])
@jwt_required()
def seed_real_project_data():
    admin_check = _require_admin()
    if admin_check:
        return admin_check

    real_data = [
        {
            "type": "Health",
            "target_amount": 500000,
            "description": (
                "Delivering free medical outreach across urban and rural Kenya, "
                "including health screenings, maternal care support, and medicine "
                "distribution to underserved communities in Nairobi's informal "
                "settlements and remote counties. We partner with local clinics and "
                "community health workers to ensure no one is turned away due to cost. "
                "Every shilling raised funds real treatment for real people — tracked "
                "transparently on this page."
            ),
        },
        {
            "type": "Education",
            "target_amount": 350000,
            "description": (
                "Keeping children in school by funding school fees, uniforms, books, "
                "and sanitary supplies for learners from low-income families across Kenya. "
                "We work directly with public primary and secondary schools in Kibera, "
                "Mathare, Turkana, and Kilifi to identify children at risk of dropping out "
                "and intervene before it happens. Education is the one investment that "
                "compounds — one child supported today becomes a family lifted tomorrow."
            ),
        },
        {
            "type": "Environment",
            "target_amount": 280000,
            "description": (
                "Restoring Kenya's natural ecosystems through tree planting, river "
                "clean-up drives, and community-led conservation education in both urban "
                "neighbourhoods and rural farmland. We have planted over 8,000 trees "
                "across 12 counties and trained 400+ community environmental champions. "
                "A healthy environment is not a luxury — it is the foundation every "
                "other development goal is built on."
            ),
        },
        {
            "type": "Community",
            "target_amount": 420000,
            "description": (
                "Strengthening the social fabric of vulnerable communities through skills "
                "training, mental health awareness, women's empowerment programs, and youth "
                "mentorship. We run regular community forums, vocational workshops, and peer "
                "support groups that give people practical tools to improve their own "
                "circumstances — not just temporary relief, but lasting capacity."
            ),
        },
        {
            "type": "Emergency",
            "target_amount": 600000,
            "description": (
                "Responding rapidly when disaster strikes — floods, drought, fire, "
                "displacement. Our emergency response team mobilises within 48 hours to "
                "deliver food parcels, clean water, temporary shelter, and trauma support "
                "to affected families across Kenya. Unlike long-term programs, emergency "
                "response is time-critical. Funds raised here are deployed immediately "
                "and reported back within 30 days of each response."
            ),
        },
        {
            "type": "Sports",
            "target_amount": 180000,
            "description": (
                "Using sport as a tool for youth development, mental health, and community "
                "cohesion in underserved areas. We fund football pitches, athletics "
                "equipment, coaching programs, and inter-county tournaments for young people "
                "aged 10-24 who would otherwise have no safe space for physical activity. "
                "Sport teaches discipline, teamwork, and resilience — skills that travel "
                "far beyond the pitch."
            ),
        },
    ]

    results = []
    for item in real_data:
        project = Project.query.filter_by(type=item["type"]).first()
        if project:
            project.description = item["description"]
            project.target_amount = item["target_amount"]
            results.append({
                "type": item["type"],
                "updated": True,
                "project_id": project.id,
            })
        else:
            results.append({
                "type": item["type"],
                "updated": False,
                "reason": "No project with this type found in the database",
            })

    db.session.commit()

    all_updated = all(r["updated"] for r in results)
    return jsonify({
        "message": "Seed complete. DELETE THIS ROUTE before next deploy.",
        "all_updated": all_updated,
        "results": results,
    }), 200


# ── EXISTING ROUTES (unchanged) ────────────────────────────────────────────

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
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    stats = _calculate_project_stats(project)

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
    all_donations = Donation.query.filter_by(status='completed').all()
    all_expenses = Expense.query.all()

    total_raised = sum(d.amount or 0 for d in all_donations)
    total_spent = sum(e.amount or 0 for e in all_expenses)

    overall_breakdown = {}
    for e in all_expenses:
        overall_breakdown[e.category] = overall_breakdown.get(e.category, 0) + e.amount

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

    project_breakdown.sort(key=lambda p: p["raised"], reverse=True)

    return jsonify({
        "total_raised": total_raised,
        "total_spent": total_spent,
        "total_remaining": total_raised - total_spent,
        "donor_count": len(all_donations),
        "project_count": len(all_projects),
        "expense_breakdown": overall_breakdown,
        "projects": project_breakdown,
    }), 200