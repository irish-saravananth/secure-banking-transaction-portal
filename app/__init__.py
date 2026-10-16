
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "main.login"


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be configured with a strong secret "
            "of at least 32 characters."
        )

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///banking.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=(
            os.environ.get("SESSION_COOKIE_SECURE", "true").lower()
            == "true"
        ),
        SESSION_COOKIE_SAMESITE="Lax",
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,
    )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "style-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'",
        )
        response.headers.setdefault(
            "X-Frame-Options", "DENY"
        )
        response.headers.setdefault(
            "X-Content-Type-Options", "nosniff"
        )
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    from app.models import User
    from app.routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app