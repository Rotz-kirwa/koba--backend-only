from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

mongo = PyMongo()
cors = CORS()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    load_dotenv()
    
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/queenkoba')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    
    mongo.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app
