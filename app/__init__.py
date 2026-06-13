from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "main.login"


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "temporary-development-key"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banking.db"

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    from app.routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
