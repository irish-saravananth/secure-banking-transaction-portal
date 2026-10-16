
from datetime import datetime, timezone

from flask_login import UserMixin

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    balance = db.Column(
        db.Float,
        default=1000.0,
        nullable=False,
    )


class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    amount = db.Column(
        db.Float,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        default="SUCCESS",
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
    )

    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
    )


@login_manager.user_loader
def load_user(user_id):
    """Load a user from the session using SQLAlchemy's current API."""
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    return db.session.get(User, user_id)