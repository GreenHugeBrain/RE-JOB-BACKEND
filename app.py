from __init__ import create_app, db
from flask_restful import Api, Resource, reqparse
from models import User, Job, Education, Experience
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from views.routes import Register, Login,  Profile, CreateJob, SearchJobs, ApplyJob, ViewApplicants, Notifications, AllJobs, JobDetail, ChatHistory, ConfirmEmail, ResendConfirmation
from flask_cors import CORS
from chat_socket import socketio

app = create_app()  
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",     # local frontend
    "https://your-frontend.com"  # your deployed frontend
]}})
socketio.init_app(app)

api = Api(app)
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(Profile, '/profile/<string:username>')
api.add_resource(CreateJob, '/jobs/create')
api.add_resource(ApplyJob, '/jobs/<int:job_id>/apply')  
api.add_resource(ViewApplicants, '/jobs/<int:job_id>/applicants')
api.add_resource(SearchJobs, '/jobs/search')
api.add_resource(Notifications, '/notifications', '/notifications/<int:notification_id>')
api.add_resource(AllJobs, '/api/jobs')
api.add_resource(JobDetail, '/jobs/<int:job_id>')
api.add_resource(ChatHistory, '/api/chat-history/<int:other_user_id>')
api.add_resource(ConfirmEmail, '/confirm-email/<token>')
api.add_resource(ResendConfirmation, '/resend-confirmation')

if __name__ == '__main__':
    socketio.run(app, debug=True)
