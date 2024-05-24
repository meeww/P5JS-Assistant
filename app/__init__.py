from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

    db.init_app(app)
    socketio.init_app(app)

    from .auth import auth_bp
    from .editor import editor_bp
    from .project import project_bp
    from .chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(editor_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(chat_bp)

    return app
