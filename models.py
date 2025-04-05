from __init__ import db, create_app
from datetime import datetime

app = create_app()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)  # Keep name as non-nullable
    email = db.Column(db.String(120), unique=True, nullable=False)  # Keep email as non-nullable
    password = db.Column(db.String(255), nullable=False)  # Keep password as non-nullable
    role = db.Column(db.String(255), nullable=False)  # Keep role as non-nullable
    job = db.Column(db.String(255), nullable=True)  # Make job nullable
    phone = db.Column(db.String(20), nullable=True)  # Make phone nullable
    address = db.Column(db.String(255), nullable=True)  # Make address nullable
    resume_file = db.Column(db.String(255), nullable=True)  # Make resume_file nullable
    cover_letter = db.Column(db.String(255), nullable=True)  # Make cover_letter nullable
    re_coins = db.Column(db.Integer, nullable=True)  # Make re_coins nullable
    company_name = db.Column(db.String(80), nullable=True)  # Make company_name nullable
    total_money = db.Column(db.Integer, nullable=True, default=0)  # Make total_money nullable
    is_confirmed = db.Column(db.Boolean, default=False)  # Field for email confirmation
    education = db.relationship('Education', backref='user', lazy=True)
    experience = db.relationship('Experience', backref='user', lazy=True)
    jobs = db.relationship('Job', backref='user', lazy=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_file = db.Column(db.String(255), nullable=True)  # Optional resume file path

    # Relationships
    user = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Fixed field type to match foreign key
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=False)
    min_budget = db.Column(db.Integer, nullable=False)  # Fixed typo from db.Colum to db.Column
    max_budget = db.Column(db.Integer, nullable=False)


class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    degree = db.Column(db.String(80), nullable=False)
    field = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    school_name = db.Column(db.String(80), nullable=False)


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position = db.Column(db.String(80), nullable=False)
    company_name = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='notifications')

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.Column(db.String(250), nullable=False)  # Store all messages as String
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Add created_at field

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')



with app.app_context():
    db.create_all()
