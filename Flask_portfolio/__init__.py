from flask import Flask
from flask_marshmallow import Marshmallow
from flask_executor import Executor
from dotenv import load_dotenv
from flask_cors import CORS
from Flask_portfolio.config import Config
import os
from Flask_portfolio.mainviews.routes import main

executor = Executor()
ma = Marshmallow()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
cors = CORS()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)

    # Initialize extensions
    executor.init_app(app)
    ma.init_app(app)
    cors.init_app(app)

    # Register blueprints
    app.register_blueprint(main)

    return app
