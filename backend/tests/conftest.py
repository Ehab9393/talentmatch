"""Pytest fixtures for TalentMatch API tests."""
import os
import sys
import tempfile
import pytest

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use a temp file database so all connections share the same data
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

os.environ["TM_DB_PATH"] = _db_path
os.environ["TM_SECRET"] = "test-secret-key"
os.environ["TM_TESTING"] = "1"  # suppresses auto-bootstrap in app.py

from database import init_db, seed_db
from app import app as flask_app, bootstrap_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create and seed the test database once for the whole session."""
    init_db()
    seed_db()
    yield
    # Cleanup temp file
    try:
        os.unlink(_db_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def app(setup_database):
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    yield flask_app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def candidate_token(client):
    """Log in as seeded candidate alice@example.com and return Bearer token."""
    res = client.post("/api/auth/login",
                      json={"email": "alice@example.com", "password": "password123"})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["token"]


@pytest.fixture(scope="session")
def employer_token(client):
    """Log in as seeded employer recruiter@google.com and return Bearer token."""
    res = client.post("/api/auth/login",
                      json={"email": "recruiter@google.com", "password": "password123"})
    assert res.status_code == 200, res.get_json()
    return res.get_json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
