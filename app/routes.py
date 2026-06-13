from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app import db
from app.models import User, Transaction

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return redirect(url_for("main.register"))


@bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return "User already exists"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("main.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:
            return "Invalid credentials"

        if not check_password_hash(
            user.password_hash,
            password
        ):
            return "Invalid credentials"

        login_user(user)

        return redirect(
            url_for("main.dashboard")
        )

    return render_template("login.html")


@bp.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user=current_user
    )


@bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():

    if request.method == "POST":

        email = request.form["email"]
        amount = float(request.form["amount"])

        receiver = User.query.filter_by(
            email=email
        ).first()

        # Validation Checks

        if not receiver:
            return "Recipient does not exist"

        if receiver.id == current_user.id:
            return "Cannot transfer money to yourself"

        if amount <= 0:
            return "Amount must be greater than zero"

        if current_user.balance < amount:
            return "Insufficient balance"

        current_user.balance -= amount
        receiver.balance += amount

        transaction = Transaction(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            amount=amount
        )

        db.session.add(transaction)
        db.session.commit()

        return redirect(
            url_for("main.dashboard")
        )

    return render_template("transfer.html")


@bp.route("/transactions")
@login_required
def transactions():

    transaction_list = Transaction.query.filter(
        (Transaction.sender_id == current_user.id)
        |
        (Transaction.receiver_id == current_user.id)
    ).all()

    return render_template(
        "transactions.html",
        transactions=transaction_list
    )


@bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("main.login")
    )
