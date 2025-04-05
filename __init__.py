import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import timedelta
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # App Configurations
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:123123@localhost/rejob',
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=10),
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME='khvtisozedelashvili@gmail.com',
        MAIL_PASSWORD='zuol hlyd ubux kayv'
    )

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    jwt = JWTManager(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    return app