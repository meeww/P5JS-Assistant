from flask import Blueprint, jsonify, send_file, session, current_app, request, send_from_directory
import os
from app.models import User
from app import db
from app.auth import login_required
from app.utils import get_file, read_logs, execute_project, upload_file, delete_file, create_file
import os

project_bp = Blueprint('project', __name__)

def list_directory(path):
    try:
        return os.listdir(path)
    except FileNotFoundError:
        return []
    
@project_bp.route('/create_project', methods=['POST'])
@login_required
def create_project_route():
    data = request.get_json()
    project_name = data['project_name']
    user_id = session['user_id']

    project_path = os.path.join('projects', str(user_id), project_name, 'src')
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        user = User.query.get(user_id)
        user.projects = user.projects + ',' + project_name if user.projects else project_name
        db.session.commit()
        return jsonify({'message': 'Project created successfully'}), 200
    return jsonify({'error': 'Project already exists'}), 400

@project_bp.route('/projects/<int:user_id>/<project_name>/src/<path:filename>')
@login_required
def serve_project_file(user_id, project_name, filename):
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    project_path = os.path.join('projects', str(user_id), project_name, 'src')
    full_file_path = os.path.join(project_path, filename)
    
    print(f"Trying to serve file from: {full_file_path}")
    print(f"Directory listing: {os.listdir(project_path)}")
    
    if not os.path.exists(full_file_path):
        print(f"File not found: {full_file_path}")
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(project_path, filename)



@project_bp.route('/projects/<user_id>/<project_name>/outputs/<path:filename>')
@login_required
def serve_output_file(user_id, project_name, filename):
    # Ensure user_id matches the session user_id
    if user_id != str(session['user_id']):
        return jsonify({'error': 'Unauthorized access'}), 403

    output_path = os.path.join(current_app.root_path, 'projects', user_id, project_name, 'outputs')
    full_file_path = os.path.join(output_path, filename)
    # remove "app\"
    full_file_path = full_file_path.replace("app\\", "")

    # Print current working directory and paths
    print(f"Current working directory: {os.getcwd()}")
    print(f"Trying to serve output file from: {full_file_path}")

    # Verify the file exists
    if not os.path.exists(full_file_path):
        print(f"File not found at: {full_file_path}")
        return jsonify({'error': 'File not found'}), 404

    # Ensure Flask serves the correct file
    return send_from_directory(output_path, filename)

@project_bp.route('/get_files', methods=['POST'])
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
        print(f"Building file structure for: {project_path}")
        
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
        print(f"Error getting files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@project_bp.route('/logs', methods=['POST'])
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
        print(f"Fetching logs from: {logs_path}")
        
        if not os.path.exists(logs_path):
            print(f"Logs not found: {logs_path}")
            return jsonify({'error': 'Logs not found'}), 404
        logs = read_logs(logs_path, data.get('start', 0), data.get('end', 999999999999999999))
        return jsonify(logs)
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@project_bp.route('/load_project', methods=['POST'])
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

@project_bp.route('/get_file', methods=['POST'])
@login_required
def request_file():
    try:
        data = request.get_json()
        project_name = data['project']
        file_path = data['file']
        user_id = session['user_id']
        user = User.query.get(user_id)

        if project_name not in (user.projects or '').split(','):
            return jsonify({'error': 'Unauthorized access'}), 403

        file_full_path = os.path.join('projects', str(user_id), project_name, 'src', file_path)
        print(f"Getting file: {file_full_path}")
        
        if not os.path.exists(file_full_path):
            return jsonify({'error': 'File not found'}), 404
        
        with open(file_full_path, 'r') as file:
            content = file.read()

        return jsonify({'content': content})
    except Exception as e:
        print(f"Error getting file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@project_bp.route('/execute', methods=['POST'])
@login_required
def request_execute():
    data = request.get_json()
    project_name = data['project']
    user_id = session['user_id']
    output = data['output']  # 'log' and/or 'image' and/or 'video'
    duration = data['duration']
    
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    output_files = execute_project(project_name, user_id, output, duration)
    return jsonify(output_files)


@project_bp.route('/upload_file', methods=['POST'])
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

@project_bp.route('/delete_file', methods=['POST'])
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

        delete_file(project_name, user_id, file_path)

        return jsonify({'success': True})
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/create_file', methods=['POST'])
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

        create_file(project_name, user_id, file_path)
        return jsonify({'success': True})
    except KeyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
