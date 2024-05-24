from flask import Blueprint, redirect, url_for, session, jsonify, render_template
from .models import User
from .auth import login_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def serve_chat():
    user_id = session['user_id']
    user = User.query.get(user_id)
    return render_template('chat/index.html', user=user)
