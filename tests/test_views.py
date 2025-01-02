import os
from unittest import TestCase
from models import db, User, favorite_player
from app import app

os.environ["DATABASE_URL"] = "postgresql:///nba_gamblr_test"
app.config["WTF_CSRF_ENABLED"] = False


def setUp(self):
    db.drop_all()
    db.create_all()

    self.client = app.test_client()
    self.testuser = User.signup(
        username="testuser",
        email="test@test.com",
        password="testpassword",
    )
    db.session.commit()


def test_homepage(self):
    """Test homepage view."""
    with self.client as client:
        resp = client.get("/")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)

        self.assertIn("NBA Gamblr", html)


def test_login(self):
    with self.client as client:
        resp = client.get("/login")
        self.assertEqual(resp.status_code, 200)
        resp = client.post(
            "/login",
            data={"username": "testuser", "password": "testpassword"},
            follow_redirects=True,
        )
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, testuser!", html)


def wrong_password(self):
    with self.client as client:
        resp = client.get("/login")
        self.assertEqual(resp.status_code, 200)
        resp = client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpassword"},
            follow_redirects=True,
        )
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Invalid credentials.", html)


def test_signup(self):
    with self.client as client:
        resp = client.get("/signup")
        self.assertEqual(resp.status_code, 200)
        resp = client.post(
            "/signup",
            data={
                "username": "signuptest",
                "password": "password",
                "email": "testuser@gmail.com",
            },
            follow_redirects=True,
        )
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, signuptest!", html)


def test_favoriting_player(self):
    with self.client as client:
        resp = client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword",
            },
            follow_redirects=True,
        )

        resp = client.get("/users/add_favorite_player/73", follow_redirects=True)

        favorites = favorite_player.query.filter_by(
            user_id=self.testuser.id, player_id=73
        ).first()

        self.assertIsNotNone(favorites)
