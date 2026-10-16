import math

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import Transaction, User

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return redirect(url_for("main.register"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or len(username) > 50:
            return "Username is required and must be at most 50 characters.", 400
        if not email or len(email) > 100:
            return "A valid email address is required.", 400
        if not password or len(password) < 12:
            return "Password must contain at least 12 characters.", 400

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        if existing_user:
            return "Username or email already exists.", 409

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "Username or email already exists.", 409

        return redirect(url_for("main.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return "Invalid credentials.", 401

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        raw_amount = request.form.get("amount", "").strip()

        try:
            amount = float(raw_amount)
        except (TypeError, ValueError):
            return "Amount must be a valid number.", 400

        if not math.isfinite(amount) or amount <= 0:
            return "Amount must be a finite number greater than zero.", 400

        receiver = User.query.filter_by(email=email).first()
        if not receiver:
            return "Recipient does not exist.", 404

        if receiver.id == current_user.id:
            return "Cannot transfer money to yourself.", 400

        if current_user.balance is None or current_user.balance < amount:
            return "Insufficient balance.", 400

        # Keep both balance updates and the transaction record in one commit.
        try:
            current_user.balance -= amount
            receiver.balance += amount

            transaction = Transaction(
                sender_id=current_user.id,
                receiver_id=receiver.id,
                amount=amount,
            )
            db.session.add(transaction)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return redirect(url_for("main.dashboard"))

    return render_template("transfer.html")


@bp.route("/transactions")
@login_required
def transactions():
    transaction_list = Transaction.query.filter(
        (Transaction.sender_id == current_user.id)
        | (Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()

    return render_template(
        "transactions.html",
        transactions=transaction_list,
    )


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))
