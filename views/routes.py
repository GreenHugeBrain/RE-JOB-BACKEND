from __init__ import create_app, db
from flask_restful import Api, Resource, reqparse
from models import User, Job, Education, Experience, JobApplication, Notification, Messages
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask import jsonify, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime  # Add this import at the top
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

app = create_app()
CORS(app)
register_parser = reqparse.RequestParser()
register_parser.add_argument('username', type=str, help='Username is required to register', required=True)
register_parser.add_argument('email', type=str, help='Email is required', required=True)
register_parser.add_argument('password', type=str, help='Password is required', required=True)
register_parser.add_argument('role', type=str, help='Role is optional')

login_parser = reqparse.RequestParser()
login_parser.add_argument('email', type=str, help='Email is required', required=True)
login_parser.add_argument('password', type=str, help='Password is required', required=True)

profile_update_parser = reqparse.RequestParser()
profile_update_parser.add_argument('name', type=str, help='Name is optional')
profile_update_parser.add_argument('job', type=str, help='Job is optional')
profile_update_parser.add_argument('phone', type=str, help='Phone is optional')
profile_update_parser.add_argument('address', type=str, help='Address is optional')
profile_update_parser.add_argument('resume_file', type=str, help='Resume file is optional')
profile_update_parser.add_argument('cover_letter', type=str, help='Cover letter is optional')
profile_update_parser.add_argument('education', type=dict, action='append', help='Education details (degree, field, etc.)')
profile_update_parser.add_argument('experience', type=dict, action='append', help='Experience details (position, company, etc.)')

message_parser = reqparse.RequestParser()
message_parser.add_argument('content', type=str, required=True, help='Message content is required')


job_post_parser = reqparse.RequestParser()
job_post_parser.add_argument('title', type=str, help='Title is required', required=True)
job_post_parser.add_argument('description', type=str, help='Description is required', required=True)
job_post_parser.add_argument('keywords', type=str, help='Keywords are required', required=True)
job_post_parser.add_argument('min_budget', type=int, help='Minimum budget is required', required=True)
job_post_parser.add_argument('max_budget', type=int, help='Maximum budget is required', required=True)

job_parser = reqparse.RequestParser()
job_parser.add_argument('title', type=str, required=True, help='Job title is required')
job_parser.add_argument('description', type=str, required=True, help='Job description is required')
job_parser.add_argument('keywords', type=str, required=True, help='Job keywords are required')
job_parser.add_argument('min_budget', type=int, required=True, help='Minimum budget is required')
job_parser.add_argument('max_budget', type=int, required=True, help='Maximum budget is required')

def get_confirmation_token_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

# Function to send confirmation email
def send_confirmation_email(user_email):
    serializer = get_confirmation_token_serializer()
    token = serializer.dumps(user_email, salt='email-confirmation-salt')
    
    # Create confirmation URL - replace with your frontend URL
    confirm_url = f"http://localhost:3000/confirm-email/{token}"
    
    msg = Message(
        'Confirm Your Email',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user_email]
    )
    
    msg.body = f'''
    Welcome to ReJob! Please confirm your email by clicking on the following link:
    
    {confirm_url}
    
    If you did not make this request then simply ignore this email.
    '''
    
    from __init__ import mail
    mail.send(msg)

# Modify the Register class to include email confirmation
class Register(Resource):
    def post(self):
        args = register_parser.parse_args()

        existing_user = User.query.filter_by(email=args['email']).first()
        if existing_user:
            return {'message': 'Email already exists'}, 400

        hashed_password = generate_password_hash(args['password'])

        new_user = User(
            name=args['username'],
            email=args['email'],
            password=hashed_password,
            role=args.get('role', 'user'),
            is_confirmed=False  # Set initial confirmation status to False
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Send confirmation email
            send_confirmation_email(new_user.email)
            
            return {
                'message': 'Registration successful. Please check your email to confirm your account.',
                'user_id': new_user.id
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error during registration: {str(e)}'}, 500

# New resource for handling email confirmation
class ConfirmEmail(Resource):
    def get(self, token):
        serializer = get_confirmation_token_serializer()
        try:
            email = serializer.loads(token, salt='email-confirmation-salt', max_age=3600)  # Token expires in 1 hour
        except:
            return {'message': 'The confirmation link is invalid or has expired.'}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'User not found.'}, 404

        if user.is_confirmed:
            return {'message': 'Account already confirmed.'}, 200

        user.is_confirmed = True
        db.session.commit()

        return {'message': 'You have confirmed your account. Thanks!'}, 200

# New resource for resending confirmation email
class ResendConfirmation(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        args = parser.parse_args()

        user = User.query.filter_by(email=args['email']).first()
        if not user:
            return {'message': 'User not found.'}, 404

        if user.is_confirmed:
            return {'message': 'Account already confirmed.'}, 400

        try:
            send_confirmation_email(user.email)
            return {'message': 'A new confirmation email has been sent.'}, 200
        except Exception as e:
            return {'message': f'Error sending confirmation email: {str(e)}'}, 500


class Login(Resource):
    def post(self):
        args = login_parser.parse_args()

        # Query the user by email
        user = User.query.filter_by(email=args['email']).first()
        if not user:
            return {'message': 'User not found'}, 404

        # Check password
        if not check_password_hash(user.password, args['password']):
            return {'message': 'Invalid credentials'}, 401

        # Generate access token
        try:
            access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=10))  # Ensure user.id is serializable
        except Exception as e:
            return {'message': f'Error generating token: {str(e)}'}, 500

        # Return the response
        return {
            'message': 'Login successful',
            'user_id': user.id,
            'access_token': access_token,
            'username': user.name,
            'role': user.role
        }, 200


from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db

class Profile(Resource):
    def get(self, username):
        user = User.query.filter_by(name=username).first()
        
        if not user:
            return {'message': 'User not found'}, 404

        jobs_list = [
            {
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'keywords': job.keywords,
                'min_budget': job.min_budget,
                'max_budget': job.max_budget
            }
            for job in user.jobs
        ]

        education_list = [
            {
                'id': edu.id,
                'degree': edu.degree,
                'field': edu.field,
                'start_date': edu.start_date.strftime('%Y-%m-%d'),
                'end_date': edu.end_date.strftime('%Y-%m-%d'),
                'school_name': edu.school_name
            }
            for edu in user.education
        ]

        experience_list = [
            {
                'id': exp.id,
                'position': exp.position,
                'company_name': exp.company_name,
                'start_date': exp.start_date.strftime('%Y-%m-%d'),
                'end_date': exp.end_date.strftime('%Y-%m-%d')
            }
            for exp in user.experience
        ]

        return {
            'username': user.name,
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'job': user.job,
            'phone': user.phone,
            'address': user.address,
            'resume_file': user.resume_file,
            'cover_letter': user.cover_letter,
            'jobs': jobs_list,
            'education': education_list,
            'experience': experience_list,
            'is_confirmed': user.is_confirmed,
            'recoins': user.re_coins,
            'totalEarnings': user.total_money,
        }, 200

    @jwt_required()  
    def put(self, username):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        target_user = User.query.filter_by(name=username).first()

        if not target_user:
            return {'message': 'User not found'}, 404
            
        if current_user.name != username:
            return {'message': 'Unauthorized'}, 403

        args = profile_update_parser.parse_args()

        if args['name']:
            current_user.name = args['name']
        if args['job']:
            current_user.job = args['job']
        if args['phone']:
            current_user.phone = args['phone']
        if args['address']:
            current_user.address = args['address']
        if args['resume_file']:
            current_user.resume_file = args['resume_file']
        if args['cover_letter']:
            current_user.cover_letter = args['cover_letter']
        if args.get('profile_image'):
            current_user.profile_image = args['profile_image']
        
        if args.get('education'):
            for edu_data in args['education']:
                edu = Education.query.get(edu_data['id']) if edu_data.get('id') else None
                if edu and edu.user_id == current_user.id:
                    edu.degree = edu_data.get('degree', edu.degree)
                    edu.field = edu_data.get('field', edu.field)
                    edu.start_date = edu_data.get('start_date', edu.start_date)
                    edu.end_date = edu_data.get('end_date', edu.end_date)
                    edu.school_name = edu_data.get('school_name', edu.school_name)
                elif not edu_data.get('id'):
                    new_edu = Education(
                        user_id=current_user.id,
                        degree=edu_data['degree'],
                        field=edu_data['field'],
                        start_date=edu_data['start_date'],
                        end_date=edu_data['end_date'],
                        school_name=edu_data['school_name']
                    )
                    db.session.add(new_edu)

        if args.get('experience'):
            for exp_data in args['experience']:
                exp = Experience.query.get(exp_data['id']) if exp_data.get('id') else None
                if exp and exp.user_id == current_user.id:
                    exp.position = exp_data.get('position', exp.position)
                    exp.company_name = exp_data.get('company_name', exp.company_name)
                    exp.start_date = exp_data.get('start_date', exp.start_date)
                    exp.end_date = exp_data.get('end_date', exp.end_date)
                elif not exp_data.get('id'):
                    new_exp = Experience(
                        user_id=current_user.id,
                        position=exp_data['position'],
                        company_name=exp_data['company_name'],
                        start_date=exp_data['start_date'],
                        end_date=exp_data['end_date']
                    )
                    db.session.add(new_exp)

        db.session.commit()
        return {'message': 'Profile updated successfully'}, 200

    @jwt_required()
    def delete(self, username):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.name != username:
            return {'message': 'Unauthorized'}, 403

        args = request.json
        record_type = args.get('type')  # "education" or "experience"
        record_id = args.get('id')
    
        if not record_type or not record_id:
            return {'message': 'Invalid request'}, 400

        if record_type == 'education':
            edu = Education.query.get(record_id)
            if edu and edu.user_id == current_user.id:
                db.session.delete(edu)
            else:
                return {'message': 'Education record not found'}, 404

        elif record_type == 'experience':
            exp = Experience.query.get(record_id)
            if exp and exp.user_id == current_user.id:
                db.session.delete(exp)
            else:
                return {'message': 'Experience record not found'}, 404

        db.session.commit()
        return {'message': f'{record_type.capitalize()} record deleted successfully'}, 200




search_parser = reqparse.RequestParser()
search_parser.add_argument('query', type=str, required=True, help='Search query is required')

class SearchJobs(Resource):
    def get(self):
        args = search_parser.parse_args()
        search_query = f"%{args['query']}%"

        jobs = Job.query.filter(
            (Job.title.ilike(search_query)) | (Job.keywords.ilike(search_query))
        ).all()

        job_list = []
        for job in jobs:
            job_list.append({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'keywords': job.keywords,
                'min_budget': job.min_budget,
                'max_budget': job.max_budget,
                'author_id': job.author
            })

        return {'jobs': job_list}, 200

class CreateJob(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        args = job_parser.parse_args()

        new_job = Job(
            author=user_id,
            title=args['title'],
            description=args['description'],
            keywords=args['keywords'],
            min_budget=args['min_budget'],
            max_budget=args['max_budget']
        )
        db.session.add(new_job)
        db.session.commit()

        return {'message': 'Job created successfully', 'job_id': new_job.id}, 201

apply_parser = reqparse.RequestParser()
apply_parser.add_argument('cover_letter', type=str, help='Cover letter is optional')
apply_parser.add_argument('resume_file', type=str, help='Resume file is optional')

class ApplyJob(Resource):
    @jwt_required()
    def post(self, job_id):
        user_id = get_jwt_identity()
        args = apply_parser.parse_args()

        job = Job.query.get(job_id)
        if not job:
            return {'message': 'Job not found'}, 404

        existing_application = JobApplication.query.filter_by(job_id=job_id, user_id=user_id).first()
        if existing_application:
            return {'message': 'You have already applied to this job'}, 400

        job_application = JobApplication(
            job_id=job_id,
            user_id=user_id,
            cover_letter=args.get('cover_letter'),
            resume_file=args.get('resume_file')
        )
        db.session.add(job_application)

        notification = Notification(
            user_id=job.author,  
            message=f'User {user_id} has applied to your job "{job.title}".'
        )
        db.session.add(notification)

        db.session.commit()
        return {'message': 'Job application submitted and notification sent'}, 201

class ViewApplicants(Resource):
    @jwt_required()
    def get(self, job_id):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        print(user)
        job = Job.query.get(job_id)
        if not job:
            return {'message': 'Job not found'}, 404
        if job.author != user_id:
            return {'message': 'You are not authorized to view applicants for this job'}, 403

        applications = JobApplication.query.filter_by(job_id=job_id).all()
        applicant_list = []
        for app in applications:
            applicant_list.append({
                'applicant_id': app.user_id,
                'username': app.user.name,
                'cover_letter': app.cover_letter,
                'resume_file': app.resume_file
            })

        return {'applicants': applicant_list}, 200

class Notifications(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
        return [{
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at
        } for n in notifications], 200

    @jwt_required()
    def put(self, notification_id):
        user_id = get_jwt_identity()
        notification = Notification.query.get(notification_id)

        if not notification or notification.user_id != user_id:
            return {'message': 'Notification not found'}, 404

        notification.is_read = True
        db.session.commit()

        return {'message': 'Notification marked as read'}, 200

class AllJobs(Resource):
    def get(self):

        jobs = Job.query.all()

        job_list = []
        for job in jobs:
            job_list.append({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'keywords': job.keywords,
                'min_budget': job.min_budget,
                'max_budget': job.max_budget,
                'author_id': job.author
            })

        return {'jobs': job_list}, 200
    
class JobDetail(Resource):
    @jwt_required()
    def get(self, job_id):
        user_id = get_jwt_identity()
        job = Job.query.get(job_id)
        user = User.query.get(user_id)
        print(user.job)
        if not job:
            return {'message': 'Job not found'}, 404

        # Retrieve applicants for the job
        applications = JobApplication.query.filter_by(job_id=job_id).all()
        applicants = [
            {
                'applicant_id': app.user_id,
                'username': app.user.name,
                'user_job': user.job,
                'user_total_earnings': user.total_money,
                'cover_letter': app.cover_letter,
                'resume_file': app.resume_file
            }
            for app in applications
        ]

        # Return job details along with applicants
        return {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'keywords': job.keywords,
            'min_budget': job.min_budget,
            'max_budget': job.max_budget,
            'author_id': job.author,
            'applicants': applicants  
        }, 200

class ChatHistory(Resource):
    @jwt_required()
    def get(self, other_user_id):
        current_user_id = get_jwt_identity()
        
        messages = Messages.query.filter(
            ((Messages.sender_id == current_user_id) & (Messages.receiver_id == other_user_id)) |
            ((Messages.sender_id == other_user_id) & (Messages.receiver_id == current_user_id))
        ).order_by(Messages.created_at.asc()).all()
        
        return {
            'messages': [{
                'id': msg.id,
                'sender_id': msg.sender_id,
                'message': msg.messages,
                'created_at': msg.created_at.isoformat()
            } for msg in messages]
        }, 200
