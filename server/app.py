#!/usr/bin/env python3
from flask import Flask, jsonify, request
import os
from server.config import db, DATABASE_URI, migrate, bcrypt, jwt,swagger, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES
from server.controller import blueprints
from flask_cors import CORS
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.debug = False
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.json.compact = False

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES


db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
jwt.init_app(app)
swagger.init_app(app)

frontend_url = "http://localhost:5173"
CORS(app, origins=["http://localhost:5173"], supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "PATCH"])

for blueprint in blueprints:
    app.register_blueprint(blueprint)


@app.route('/')
def index():
    """
    A simple Hello World endpoint
    ---
    responses:
      200:
        description: Returns Hello World message
        examples:
          application/json: {"message": "Hello World"}
    """

    return jsonify({"message": "Hope Connect backend is running"}), 200



if __name__ == '__main__':
    app.run(port=5000, debug=True)
    
