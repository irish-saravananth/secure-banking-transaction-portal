from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banking.db"

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)

    from app.models import User

    with app.app_context():
        db.create_all()

    return app
