# Imports
from flask import jsonify
from marshmallow import fields, validate
from flask_marshmallow import Marshmallow, Schema
from flask import Flask, request, jsonify
from flask_expects_json import expects_json
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.validators import DataRequired
import smtplib
import bleach
from email.message import EmailMessage
from flask_executor import Executor
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired
from wtforms import SelectField
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
admin = Admin(app, template_mode='bootstrap3', url="/hacker")
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_if_not_found')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
db = SQLAlchemy(app)
executor = Executor(app)
ma = Marshmallow(app)
load_dotenv()


class EmailSchema(Schema):
    fullname = fields.String(required=True)
    subject = fields.String(required=True)
    message = fields.String(required=True)
    email = fields.Email(required=True, validate=validate.Email())

# Database Models


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    project_tag = db.Column(db.String(50), nullable=False)
    objective = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tools_and_technology = db.Column(db.String(100), nullable=False)
    repo_link = db.Column(db.String(200))
    url = db.Column(db.String(300), default="Xendpal.com.ng")
    extra = db.Column(db.String(200), nullable=True)
    # Relationships
    image_files = db.relationship('ImageFile', backref='portfolio', lazy=True)
    video_files = db.relationship('VideoFile', backref='portfolio', lazy=True)

    def __repr__(self):
        return f"Portfolio('{self.project_name}', '{self.project_tag}', '{self.objective}', '{self.date}', '{self.description}', '{self.tools_and_technology}', '{self.repo_link}', '{self.video_file}')"


class ImageFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(200), nullable=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey(
        'portfolio.id'), nullable=False)

    def __repr__(self):
        return f"ImageFile('{self.image_file}')"


class VideoFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_file = db.Column(db.String(200), nullable=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey(
        'portfolio.id'), nullable=False)

    def __repr__(self):
        return f"ImageFile('{self.image_file}')"


class Skills(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skills = db.Column(db.String(200), nullable=True)


class PortfolioForm(FlaskForm):
    # Define the fields for each column in your model
    project_name = StringField('Project Name', validators=[DataRequired()])
    project_tag = StringField('Project Tag', validators=[DataRequired()])
    objective = TextAreaField('Objective', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    tools_and_technology = StringField(
        'Tools and Technology', validators=[DataRequired()])
    repo_link = StringField('Repository Link')
    extra = StringField('Extra')
    url = StringField('url')


class ImageForm(FlaskForm):
    image_files = MultipleFileField('Image Files')
    portfolio_id = SelectField('Portfolio', coerce=int)

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.portfolio_id.choices = [
            (portfolio.id, portfolio.project_name) for portfolio in Portfolio.query.all()]


class VideoForm(FlaskForm):
    video_files = MultipleFileField('Video Files')
    portfolio_id = SelectField('Portfolio', coerce=int)

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        self.portfolio_id.choices = [
            (portfolio.id, portfolio.project_name) for portfolio in Portfolio.query.all()]


class SkillsView(ModelView):
    column_list = ['id',  'skills']


# Define the static folder path for images and videos
IMAGE_FOLDER = os.path.join(app.root_path, "static/images")
VIDEO_FOLDER = os.path.join(app.root_path, "static/videos")
# Create a ModelView class for the Portfolio model


class PortfolioModelView(ModelView):
    # Use the custom form class
    form = PortfolioForm
    # Override the on_model_change method


class ImageView(ModelView):

    form = ImageForm

    def on_model_change(self, form, model, is_created):
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)

        image_files = form.image_files.data
        selected_portfolio_id = form.portfolio_id.data  # Get the selected portfolio_id

        if len(image_files) > 0:
            for image_file in image_files:
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(IMAGE_FOLDER, filename))
                if filename:
                    print(
                        f"Filename: {filename}, Portfolio ID: {selected_portfolio_id}")
                    db_image_file = ImageFile(
                        image_file=str(filename),
                        portfolio_id=selected_portfolio_id  # Use the selected portfolio_id
                    )
                    db.session.add(db_image_file)
                    print("DB Object:", db_image_file)

                    db.session.commit()  # Explicitly commit the changes

    def on_model_delete(self, model):
        # Get the image files and video files from the model
        image_files = model.image_files

        # Loop through the image files
        for image_file in image_files:
            # Get the filename
            filename = image_file.image_file
            # Delete the file from the static folder
            os.remove(os.path.join(IMAGE_FOLDER, filename))
            # Delete the ImageFile instance from the database session
            db.session.delete(image_file)

        db.session.commit()  # Explicitly commit the changes


class VideoView(ModelView):
    form = VideoForm

    def on_model_change(self, form, model, is_created):
        if not os.path.exists(VIDEO_FOLDER):
            os.makedirs(VIDEO_FOLDER)

        video_files = form.video_files.data
        selected_portfolio_id = form.portfolio_id.data  # Get the selected portfolio_id

        if len(video_files) > 0:
            for video_file in video_files:
                filename = secure_filename(video_file.filename)
                video_file.save(os.path.join(VIDEO_FOLDER, filename))
                if filename:
                    db_video_file = VideoFile(
                        video_file=str(filename),
                        portfolio_id=selected_portfolio_id  # Use the selected portfolio_id
                    )
                    db.session.add(db_video_file)
                    print("DB Object:", db_video_file)
                    db.session.commit()  # Explicitly commit the changes

    def on_model_delete(self, model):
        video_files = model.video_files

        # Loop through the video files
        for video_file in video_files:
            # Get the filename
            filename = video_file.video_file
            # Delete the file from the static folder
            os.remove(os.path.join(VIDEO_FOLDER, filename))
            # Delete the VideoFile instance from the database session
            db.session.delete(video_file)

        db.session.commit()  # Explicitly commit the changes


admin.add_view(PortfolioModelView(Portfolio, db.session))
admin.add_view(SkillsView(Skills, db.session))
admin.add_view(ImageView(ImageFile, db.session))
admin.add_view(VideoView(VideoFile, db.session))


def send_me_the_email(*args, **kwargs):
    message_content = kwargs.get('message', '')
    email = kwargs.get('email', '')
    full_name = kwargs.get('full_name', '')
    subject = kwargs.get('subject', '')

    message = EmailMessage()
    message.set_content(
        f"MESSAGE:{bleach.clean(message_content)}\n EMAIL:{email} \n NAME:{full_name}")
    message['Subject'] = subject.upper()
    message['From'] = email
    message['To'] = os.environ.get("EMAIL")

    email_server = smtplib.SMTP("smtp.gmail.com", 587)
    email_server.starttls()
    email_server.login(os.environ.get("EMAIL"), os.environ.get("PASSKEY"))
    email_server.send_message(message)


RequestSchema = EmailSchema(many=True)


@app.route('/send_email', methods=['POST'])
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
    executor.submit(send_me_the_email, **dictionary)
    return jsonify({"status": "Email sent"}), 201


@app.route('/')
def hello_world():
    db.create_all()
    return 'Hello, World!'


@app.route('/portfolio/<string:portfolio_title>', methods=['GET'])
def get_portfolio_by_id(portfolio_title):
    # Query the Portfolio model to find a record with the given ID
    portfolio = Portfolio.query.filter(
        Portfolio.project_name.ilike(f"%{portfolio_title}%")).first()

    # Query related ImageFiles and VideoFiles
    image_files = ImageFile.query.filter_by(portfolio_id=portfolio.id).all()
    video_files = VideoFile.query.filter_by(portfolio_id=portfolio.id).all()

    # Convert ImageFiles and VideoFiles to lists of filenames
    image_filenames = [image_file.image_file for image_file in image_files]
    video_filenames = [video_file.video_file for video_file in video_files]

    # Create a dictionary to hold the portfolio details
    portfolio_details = []

    portfolio_details.append(
        {
            'id': portfolio.id,
            'project_name': portfolio.project_name,
            'project_tag': portfolio.project_tag,
            'objective': portfolio.objective,
            'date': portfolio.date,
            'description': portfolio.description,
            'tools_and_technology': portfolio.tools_and_technology,
            'repo_link': portfolio.repo_link,
            'url': portfolio.url,
            'extra': portfolio.extra,
            'image_files': image_filenames,
            'video_files': video_filenames
        }
    )

    return jsonify(portfolio_details), 200


@app.route('/projects', methods=['GET'])
def get_all_first_image_details():
    # Initialize an empty list to hold the data for all portfolios
    all_data = []

    # Query all Portfolio records
    all_portfolios = Portfolio.query.all()

    if not all_portfolios:
        return jsonify({"error": "No portfolios found"}), 404

    for portfolio in all_portfolios:
        # Get the first ImageFile for this portfolio
        first_image = ImageFile.query.filter_by(
            portfolio_id=portfolio.id).offset(1).first()

        # Prepare the data for this portfolio
        if first_image:
            data = {
                "first_image_file": first_image.image_file,
                "portfolio_project_name": portfolio.project_name,
                "portfolio_description": portfolio.extra,
                "portfolio_url": portfolio.url,
                "repo_link": portfolio.repo_link,
                "id": portfolio.id
            }
        else:
            data = {
                "first_image_file": None,
                "portfolio_project_name": portfolio.project_name,
                "portfolio_description": portfolio.description
            }

        # Append the data to the list
        all_data.append(data)

    return jsonify(all_data), 200


# Main Entry Point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
