from flask import Blueprint, redirect, url_for, session, jsonify, render_template
from app.models import User
from app import socketio
from app.watchdog_handler import start_monitoring
from app.auth import login_required
import os

editor_bp = Blueprint('editor', __name__)

@editor_bp.route('/editor/<project_name>')
@login_required
def serve_editor(project_name):
    user_id = session['user_id']
    user = User.query.get(user_id)
    if project_name not in (user.projects or '').split(','):
        return jsonify({'error': 'Unauthorized access'}), 403

    project_path = os.path.join('projects', str(user_id), project_name, 'src')
    start_monitoring(project_path)  # Start monitoring the project path

    return render_template('editor/index.html', project_name=project_name, user_id=user_id)
