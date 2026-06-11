from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from werkzeug.security import generate_password_hash

from app import db
from app.models import User

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

        return "User Registered Successfully"

    return render_template("register.html")
