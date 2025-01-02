import os
from unittest import TestCase
from models import db, User, favorite_player, SignUpForm
from sqlalchemy.exc import IntegrityError

os.environ["DATABASE_URL"] = "postgresql:///nba_gamblr_test"

from app import app


class UserModelTestCase(TestCase):
    """Test cases for User model."""

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.client = app.test_client()
        self.testuser = User.signup(
            username="testuser", password="testpassword", email="test@test.com"
        )
        db.session.commit()

    def tearDown(self):
        db.session.rollback()


def test_authentication(self):
    """Test authentication of user."""

    user = User.authenticate("testuser", "testpassword")
    self.assertEqual(user, self.testuser)

    wrong_password = User.authenticate("testuser", "wrongpassword")
    self.assertFalse(wrong_password)

    wrong_username = User.authenticate("wronguser", "testpassword")
    self.assertFalse(wrong_username)


def test_user_signup(self):
    """Test user signup."""
    new_user = User.signup(
        username="newuser", email="new@test.com", password="password123"
    )
    db.session.commit()

    self.assertIsNotNone(new_user)
    self.assertNotEqual(new_user.password, "password123")
    self.assertEqual(new_user.email, "new@test.com")


def test_duplicate_user(self):
    """Test duplicate user signup"""

    with self.assertRaises(IntegrityError):
        dup_user = User.signup(
            username="testuser", email="test@gmail.com", password="testpassword"
        )
        db.session.commit()

    db.session.rollback()


def test_short_password(self):
    """Test password that is too short"""
    form = SignUpForm(
        data={"username": "newuser", "email": "new@test.com", "password": "hi"}
    )
    self.assertFalse(form.validate())


def test_bad_email(self):
    """Test that form doesn't accept non-email entry"""
    form = SignUpForm(
        data={"username": "newuser", "email": "hello", "password": "password123"}
    )
    self.assertFalse(form.validate())
