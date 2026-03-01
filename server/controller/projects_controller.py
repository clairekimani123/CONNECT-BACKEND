from flask import Blueprint, request, jsonify
from server.models import Project
from server.config import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime


projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('', methods=['GET'])
def get_projects():
    """
    Get all projects
    ---
    responses:
      200:
        description: List of all projects
        examples:
          application/json: [{"id": 1, "type": "Construction", "description": "Building project", "date": "2024-06-29", "image_url": "http://example.com/image.png"}]
    """
    projects = [project.to_dict() for project in Project.query.all()]
    return jsonify(projects), 200


@projects_bp.route('', methods=['POST'])
def create_project():
    """
    Create a new project
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - type
            - description
            - date
            - image_url
          properties:
            type:
              type: string
            description:
              type: string
            date:
              type: string
              format: date
            image_url:
              type: string
    responses:
      201:
        description: Project created successfully
      422:
        description: Missing or invalid project data
    """
    
    data = request.get_json()
  
    if not data:
        return jsonify({"error": "Missing project data"}), 422

    try:
        date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()

        new_project = Project(
            type=data["type"],
            description=data["description"],
            date=date_obj,
            image_url=data["image_url"]
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
def delete_project(project_id):
    """
    Delete a project by ID (Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: project_id
        in: path
        type: integer
        required: true
        description: ID of the project to delete
    responses:
      200:
        description: Project deleted successfully
      404:
        description: Project not found
      422:
        description: Unauthorized user or other error
    """
    
   

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
