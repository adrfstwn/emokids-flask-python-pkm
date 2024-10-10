from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
socketio = SocketIO(cors_allowed_origins="*") 
login.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        from apps import routes, models
        

    return app
