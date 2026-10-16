import re

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Transaction, User


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SECRET_KEY",
        "test-only-secret-key-for-pytest-123456789",
    )
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite:///{tmp_path / 'test.db'}",
    )
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")

    application = create_app()
    application.config.update(TESTING=True)

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_token(client, path):
    response = client.get(path)
    assert response.status_code == 200

    # Extract the token from the form without assuming a specific
    # HTML attribute order or whitespace.
    html = response.get_data(as_text=True)
    match = re.search(
        r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)',
        html,
    )
    if not match:
        # Support the opposite attribute order.
        match = re.search(
            r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf_token["\']',
            html,
        )

    assert match, f"No CSRF token found in {path}"
    return match.group(1)


def register(client, username, email, password="TestPassword123!"):
    token = csrf_token(client, "/register")
    return client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": username,
            "email": email,
            "password": password,
        },
        follow_redirects=False,
    )


def login(client, email, password="TestPassword123!"):
    token = csrf_token(client, "/login")
    return client.post(
        "/login",
        data={
            "csrf_token": token,
            "email": email,
            "password": password,
        },
        follow_redirects=False,
    )


def transfer(client, email, amount):
    token = csrf_token(client, "/transfer")
    return client.post(
        "/transfer",
        data={
            "csrf_token": token,
            "email": email,
            "amount": str(amount),
        },
        follow_redirects=False,
    )


def create_user(username, email, balance=1000.0):
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash("TestPassword123!"),
        balance=balance,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_register_page_returns_security_headers(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert response.headers.get("Content-Security-Policy")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert (
        response.headers.get("Referrer-Policy")
        == "strict-origin-when-cross-origin"
    )
    assert response.headers.get("Permissions-Policy")
    assert response.headers.get("Cache-Control") == "no-store"


def test_session_cookie_has_http_only_and_same_site(client):
    response = client.get("/register")

    session_cookie = next(
        (
            value
            for value in response.headers.getlist("Set-Cookie")
            if value.startswith("session=")
        ),
        None,
    )

    assert session_cookie is not None
    assert "HttpOnly" in session_cookie
    assert "SameSite=Lax" in session_cookie


def test_register_rejects_post_without_csrf_token(client):
    response = client.post(
        "/register",
        data={
            "username": "test-user",
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 400


def test_registration_and_duplicate_rejection(client):
    response = register(client, "alice", "ALICE@example.com")
    assert response.status_code == 302

    duplicate = register(client, "alice", "alice@example.com")
    assert duplicate.status_code == 409


def test_registration_rejects_short_password(client):
    response = register(
        client,
        "short-password",
        "short@example.com",
        password="short",
    )
    assert response.status_code == 400


def test_login_accepts_valid_credentials_and_rejects_invalid(client):
    assert register(client, "alice", "alice@example.com").status_code == 302

    bad_login = login(client, "alice@example.com", "wrong-password")
    assert bad_login.status_code == 401

    good_login = login(client, "alice@example.com")
    assert good_login.status_code == 302
    assert "/dashboard" in good_login.headers["Location"]


def test_transfer_updates_balances_and_records_transaction(app, client):
    with app.app_context():
        alice = create_user("alice", "alice@example.com", 1000.0)
        create_user("bob", "bob@example.com", 1000.0)
        alice_id = alice.id

    assert login(client, "alice@example.com").status_code == 302

    response = transfer(client, "bob@example.com", "25")
    assert response.status_code == 302

    with app.app_context():
        alice = db.session.get(User, alice_id)
        bob = User.query.filter_by(email="bob@example.com").one()
        transaction = Transaction.query.one()

        assert alice.balance == pytest.approx(975.0)
        assert bob.balance == pytest.approx(1025.0)
        assert transaction.amount == pytest.approx(25.0)
        assert transaction.sender_id == alice.id
        assert transaction.receiver_id == bob.id


@pytest.mark.parametrize("amount", ["abc", "nan", "inf", "-1", "0"])
def test_transfer_rejects_invalid_amounts_without_changing_balances(
    app, client, amount
):
    with app.app_context():
        alice = create_user("alice", "alice@example.com", 1000.0)
        create_user("bob", "bob@example.com", 1000.0)
        alice_id = alice.id

    assert login(client, "alice@example.com").status_code == 302

    response = transfer(client, "bob@example.com", amount)
    assert response.status_code == 400

    with app.app_context():
        alice = db.session.get(User, alice_id)
        bob = User.query.filter_by(email="bob@example.com").one()

        assert alice.balance == pytest.approx(1000.0)
        assert bob.balance == pytest.approx(1000.0)
        assert Transaction.query.count() == 0


def test_transfer_rejects_missing_recipient(app, client):
    with app.app_context():
        create_user("alice", "alice@example.com")

    assert login(client, "alice@example.com").status_code == 302

    response = transfer(client, "missing@example.com", "10")
    assert response.status_code == 404


def test_transfer_rejects_self_transfer(app, client):
    with app.app_context():
        create_user("alice", "alice@example.com")

    assert login(client, "alice@example.com").status_code == 302

    response = transfer(client, "alice@example.com", "10")
    assert response.status_code == 400


def test_transfer_rejects_insufficient_balance(app, client):
    with app.app_context():
        alice = create_user("alice", "alice@example.com", 10.0)
        create_user("bob", "bob@example.com", 1000.0)
        alice_id = alice.id

    assert login(client, "alice@example.com").status_code == 302

    response = transfer(client, "bob@example.com", "11")
    assert response.status_code == 400

    with app.app_context():
        alice = db.session.get(User, alice_id)
        bob = User.query.filter_by(email="bob@example.com").one()

        assert alice.balance == pytest.approx(10.0)
        assert bob.balance == pytest.approx(1000.0)
        assert Transaction.query.count() == 0


def test_logout_requires_post_and_csrf_token(client):
    assert register(client, "alice", "alice@example.com").status_code == 302
    assert login(client, "alice@example.com").status_code == 302

    assert client.get("/logout").status_code == 405

    rejected = client.post("/logout")
    assert rejected.status_code == 400

    token = csrf_token(client, "/dashboard")
    response = client.post("/logout", data={"csrf_token": token})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    assert client.get("/dashboard").status_code == 302
