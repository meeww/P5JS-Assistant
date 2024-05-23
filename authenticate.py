from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_oauthlib.client import OAuth
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=os.getenv('GOOGLE_CLIENT_ID'),
    consumer_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    projects = db.Column(db.Text, nullable=True)  # Can be JSON or other format

# Ensure the database is created within the application context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.pop('google_token')
    session.pop('user_id')
    return redirect(url_for('index'))

@app.route('/login/authorized')
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

    return redirect(url_for('menu'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/menu')
@login_required
def menu():
    user_id = session['user_id']
    user = User.query.get(user_id)
    projects = (user.projects or '').split(',')
    return render_template('menu/index.html', projects=projects)

@app.route('/create_project', methods=['POST'])
@login_required
def create_project_route():
    data = request.get_json()
    project_name = data['project_name']
    user_id = session['user_id']

    project_path = f'./projects/{user_id}/{project_name}/'
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        user = User.query.get(user_id)
        user.projects = user.projects + ',' + project_name if user.projects else project_name
        db.session.commit()
        return jsonify({'message': 'Project created successfully'}), 200
    return jsonify({'error': 'Project already exists'}), 400

@app.route('/load_project', methods=['POST'])
@login_required
def load_project():
    data = request.get_json()
    project_name = data['project_name']
    user_id = session['user_id']
    user = User.query.get(user_id)

    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    return jsonify({'message': 'Project loaded successfully'}), 200

@app.route('/get_file', methods=['POST'])
@login_required
def request_file():
    try:
        data = request.get_json()
        project_name = data['project']
        file = data['file']
        user_id = session['user_id']
        
        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

        return get_file(project_name, file)
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
