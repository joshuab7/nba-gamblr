from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, Email
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class SearchForm(FlaskForm):
    search = StringField(
        "Player Search",
        render_kw={"placeholder": "Search by first OR last name"},
        validators=[
            DataRequired(),
        ],
    )
    submit = SubmitField("Search")


class LineCheckForm(FlaskForm):
    bet_line = StringField(
        "Betting Line",
        validators=[DataRequired()],
    )
    stat_cat = SelectField(
        "Stat Category",
        choices=[("points"), ("rebounds"), ("assists")],
    )
    submit = SubmitField("Check Line!")


class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    email = EmailField("Email", validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[Length(min=6)])


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    favorite_player = db.relationship("favorite_player", backref="users")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(
        cls,
        username,
        email,
        password,
    ):
        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class favorite_player(db.Model):
    __tablename__ = "favorite_players"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
