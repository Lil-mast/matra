"""Tests for authentication endpoints."""

import sys
import os
import pytest

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from models import db as _db


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_HOURS = 1


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, username="nurse1", password="pass1234", role="chw"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "role": role},
    )


def _login(client, username="nurse1", password="pass1234"):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


class TestRegister:
    def test_register_success(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert "token" in data
        assert data["role"] == "chw"

    def test_register_duplicate(self, client):
        _register(client)
        resp = _register(client)
        assert resp.status_code == 409

    def test_register_missing_fields(self, client):
        resp = client.post("/api/auth/register", json={"username": ""})
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        _register(client)
        resp = _login(client)
        assert resp.status_code == 200
        assert "token" in resp.get_json()

    def test_login_wrong_password(self, client):
        _register(client)
        resp = _login(client, password="wrong")
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = _login(client, username="nobody")
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_metrics_without_token(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 401

    def test_metrics_with_token(self, client):
        reg = _register(client)
        token = reg.get_json()["token"]
        resp = client.get(
            "/api/metrics", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

    def test_sync_with_token(self, client):
        reg = _register(client)
        token = reg.get_json()["token"]
        intake = {
            "age": 28, "parity": 1,
            "systolic_bp": 120, "diastolic_bp": 80, "pulse": 78,
            "bleeding": 0, "fever": False, "convulsions": False,
            "reduced_fetal_movement": False, "anemia": False,
        }
        resp = client.post(
            "/api/sync",
            json=[intake],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["synced"] == 1
