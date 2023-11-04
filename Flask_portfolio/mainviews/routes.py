from flask import Blueprint,request, jsonify
import bleach
from marshmallow import fields, validate
from flask_marshmallow import Schema
import os
from Flask_portfolio.utils import send_me_the_email
import json
import asyncio

json_file_path = os.path.join(os.path.dirname(__file__), 'db.json')


main = Blueprint('main', __name__)

class EmailSchema(Schema):
    fullname = fields.String(required=True)
    subject = fields.String(required=True)
    message = fields.String(required=True)
    email = fields.Email(required=True, validate=validate.Email())


@main.route('/send_email', methods=['POST'])
def send_email():
    schema = EmailSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"errors": errors}), 400

    full_name = bleach.clean(request.json.get("fullname"))
    subject = bleach.clean(request.json.get("subject"))
    email = bleach.clean(request.json.get("email"))
    message = bleach.clean(request.json.get("message"))
    dictionary = {
        "full_name": full_name,
        "subject": subject,
        "email": email,
        "message": message,
    }

    # Define an async function to send the email
    
    send_me_the_email(**dictionary)

    return jsonify({"status": "Email sent"}), 201



@main.route('/')
def hello_world():
    return 'Hello, World!'


@main.route('/portfolio/<string:portfolio_title>', methods=['GET'])
def get_portfolio_by_title(portfolio_title):
    # Load data from the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Search for a portfolio with a matching project_name
    portfolio = next(
        (item for item in data if item["project_name"].lower() == portfolio_title.lower()), None)

    if portfolio:
        return jsonify(portfolio), 200
    else:
        return jsonify({"error": "Portfolio not found"}), 404


@main.route('/projects', methods=['GET'])
def get_all_project_details():
    # Load data from the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    result = []

    for project in data:
        first_image = project['image_file'][0] if project['image_file'] else None

        project_data = {
            "first_image_file": first_image,
            "portfolio_project_name": project['project_name'],
            "portfolio_description": project['extra'],
            "portfolio_url": project['url'],
            "repo_link": project['repo_link'],
            "id": project['id']
        }

        result.append(project_data)

    return jsonify(result), 200
