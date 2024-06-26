from flask import Flask, redirect, url_for, session, request, jsonify, render_template, send_from_directory
from flask_oauthlib.client import OAuth
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import os
from project import get_file, read_logs, execute_project, upload_file, delete_file, create_file
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)


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


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, project_path):
        self.project_path = project_path

    def on_any_event(self, event):
        # Emit an event to the client when any file system event is detected
        socketio.emit('file_change', {'message': 'File system has changed'})

def start_monitoring(project_path):
    event_handler = FileChangeHandler(project_path)
    observer = Observer()
    observer.schedule(event_handler, project_path, recursive=True)
    observer.start()


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

    project_path = f'./projects/{user_id}/{project_name}/src'
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        user = User.query.get(user_id)
        user.projects = user.projects + ',' + project_name if user.projects else project_name
        db.session.commit()
        return jsonify({'message': 'Project created successfully'}), 200
    return jsonify({'error': 'Project already exists'}), 400

@app.route('/editor/<project_name>')
@login_required
def serve_editor(project_name):
    user_id = session['user_id']
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    project_path = os.path.join('projects', str(user_id), project_name, 'src')
    start_monitoring(project_path)  # Start monitoring the project path

    return render_template('editor/index.html', project_name=project_name)


@app.route('/projects/<project_name>/src/<path:filename>')
@login_required
def serve_project_file(project_name, filename):
    user_id = session['user_id']
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    project_path = os.path.join('projects', str(user_id), project_name, 'src')
    if not os.path.exists(os.path.join(project_path, filename)):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(project_path, filename)

@app.route('/projects/<project_name>/outputs/<path:filename>')
@login_required
def serve_output_file(project_name, filename):
    user_id = session['user_id']
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    output_path = os.path.join('projects', str(user_id), project_name, 'outputs')
    if not os.path.exists(os.path.join(output_path, filename)):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(output_path, filename)

@app.route('/get_files', methods=['POST'])
@login_required
def get_files():
    try:
        data = request.get_json()
        project_name = data['project_name']
        user_id = session['user_id']
        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

        project_path = os.path.join('projects', str(user_id), project_name, 'src')
        
        def build_file_structure(root_path):
            file_structure = {}
            for root, dirs, files in os.walk(root_path):
                rel_path = os.path.relpath(root, root_path)
                if rel_path == ".":
                    rel_path = ""
                parts = rel_path.split(os.sep) if rel_path else []
                current = file_structure
                for part in parts:
                    current = current.setdefault(part, {})
                for file_name in files:
                    current.setdefault(file_name, file_name)
                for dir_name in dirs:
                    current.setdefault(dir_name, {})
            return file_structure
        
        file_structure = build_file_structure(project_path)
        return jsonify(file_structure)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['POST'])
@login_required
def get_logs():
    try:
        data = request.get_json()
        project_name = data['project_name']
        user_id = session['user_id']
        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

        logs_path = os.path.join('projects', str(user_id), project_name, 'outputs', 'logs.db')
        if not os.path.exists(logs_path):
            return jsonify({'error': 'Logs not found'}), 404
        logs = read_logs(logs_path, data.get('start', 0), data.get('end', 999999999999999999))
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@app.route('/load_project', methods=['POST'])
@login_required
def load_project():
    try:
        data = request.get_json()
        project_name = data['project_name']
        user_id = session['user_id']
        user = User.query.get(user_id)

        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

        return jsonify({'message': 'Project loaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
            # remove project name in the file path if it exists
        if project_name in file_path:
            file_path = file_path.replace(project_name, '').lstrip('/')


        file_content = get_file(user_id, project_name, file)
        return file_content
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/execute', methods=['POST'])
@login_required
async def request_execute():
    data = request.get_json()
    project_name = data['project']
    user_id = session['user_id']
    output = data['output']  # 'log' and/or 'image' and/or 'video'
    duration = data['duration']
    print(project_name, output, duration)
    result = await execute_project(project_name, user_id, outputs=output, duration=duration)
    print(result)
    return jsonify(result)

@app.route('/upload_file', methods=['POST'])
@login_required
def request_upload():
    try:
        data = request.get_json()
        project_name = data['project_name']
        file = data['file']
        content = data['content']
        user_id = session['user_id']

        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403
            

        return jsonify(upload_file(project_name, user_id, file, content))
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_file', methods=['POST'])
@login_required
def request_delete_file():
    try:
        data = request.get_json()
        project_name = data['project_name']
        file_path = data['file']
        user_id = session['user_id']



        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

    # remove project name in the file path if it exists
        if project_name in file_path:
            file_path = file_path.replace(project_name, '').lstrip('/')

        delete_file(project_name, user_id, file_path)
        

        return jsonify({'success': True})
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/create_file', methods=['POST'])
@login_required
def request_create_file():
    try:
        data = request.get_json()
        project_name = data['project_name']
        file_path = data['file']
        user_id = session['user_id']

        user = User.query.get(user_id)
        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        # remove project name in the file path if it exists
        if project_name in file_path:
            file_path = file_path.replace(project_name, '').lstrip('/')

        create_file(project_name, user_id, file_path)
        return jsonify({'success': True})
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, debug=True)