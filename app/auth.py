from flask import Blueprint, redirect, url_for, session, request, jsonify, render_template
from flask_oauthlib.client import OAuth
from .models import User, db
import os

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

google = oauth.remote_app(
    'google',
    consumer_key='GOOGLE_CLIENT_ID',
    consumer_secret='GOOGLE_CLIENT_SECRET',
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@auth_bp.route('/login')
def login():
    return google.authorize(callback=url_for('auth.authorized', _external=True))

@auth_bp.route('/logout')
def logout():
    session.pop('google_token')
    session.pop('user_id')
    return redirect(url_for('auth.index'))

@auth_bp.route('/login/authorized')
def authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    session['google_token'] = (response['access_token'], '')
    user_info = google.get('userinfo')
    user_email = user_info.data['email']

    user = User.query.filter_by(email=user_email).first()
    if user is None:
        user = User(email=user_email)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id

    return redirect(url_for('auth.menu'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('auth.menu'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/menu')
@login_required
def menu():
    user_id = session['user_id']
    user = User.query.get(user_id)
    projects = (user.projects or '').split(',')
    return render_template('menu/index.html', projects=projects)

@auth_bp.route('/create_project', methods=['POST'])
@login_required
def create_project_route():
    data = request.get_json()
    project_name = data['project_name']
    user_id = session['user_id']

    project_path = f'./projects/{user_id}/{project_name}/src'
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        user = User.query.get(user_id)
        user.projects = user.projects + ',' + project_name if user.projects else project_name
        db.session.commit()
        return jsonify({'message': 'Project created successfully'}), 200
    return jsonify({'error': 'Project already exists'}), 400
