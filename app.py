from dotenv import load_dotenv
import os
import requests
from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    session,
    flash,
    request,
    g,
)
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from balldontlie import BalldontlieAPI
from models import (
    SearchForm,
    LineCheckForm,
    SignUpForm,
    LoginForm,
    User,
    favorite_player,
    db,
)
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-secret-key")
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt = Bcrypt(app)

API_KEY = os.environ.get("BALLDONTLIE_API_KEY")
api = BalldontlieAPI(api_key=API_KEY)
teams_response = api.nba.teams.list()
teams_dict = teams_response.model_dump()

teams = {
    team["id"]: team["full_name"] for team in teams_dict["data"] if team["id"] <= 30
}

headers = {
    "x-rapidapi-key": os.environ.get("RAPIDAPI_KEY"),
    "x-rapidapi-host": "api-nba-v1.p.rapidapi.com",
}

url = "https://api-nba-v1.p.rapidapi.com/standings"

CURR_USER_KEY = "curr_user"

with app.app_context():
    db.create_all()


##############Ideas###########
# logged in users can add favorite players(can be displayed in table?)
# favorite players last 5 [-5:] games will be showed on bar graph compared to other favorite players
@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    session[CURR_USER_KEY] = user.id


def do_logout():
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/", methods=["GET", "POST"])
def homepage():
    form = SearchForm()
    favorite_players = []
    if g.user:
        favorite_players = favorite_player.query.filter_by(user_id=g.user.id).all()
    players_data = []
    for player in favorite_players:
        try:
            player_info = api.nba.players.get(player.player_id)
            player_dict = player_info.model_dump()
            player_data = player_dict["data"]
            player_info = {
                "id": player_data["id"],
                "name": f"{player_data['first_name']} {player_data['last_name']}",
                "position": player_data["position"],
                "country": player_data["country"],
            }
            players_data.append(player_info)
        except Exception as e:
            print(f"Error fetching player {player.player_id}: {str(e)}")

    if form.validate_on_submit():
        name = form.search.data
        return redirect(f"active-player/{name}")
    else:
        return render_template("homepage.html", form=form, players=players_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", "danger")

    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()
            do_login(user)
            return redirect("/")
        except IntegrityError:
            flash("Username already taken", "danger")
            return render_template("signup.html", form=form)
    else:
        return render_template("signup.html", form=form)


@app.route("/standings/<division>")
def division_standings(division):
    querystring = {"league": "standard", "season": "2024", "division": division.lower()}
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    standings = data["response"]
    return render_template("division.html", standings=standings)


@app.route("/active-player/<name>")
def player_search(name):
    name_search = api.nba.players.list_active(search=name)
    favorited_ids = []
    if g.user:
        favorite_players = favorite_player.query.filter_by(user_id=g.user.id).all()
        player_dict = name_search.model_dump()
        player_data = player_dict["data"]
        favorited_ids = [fav.id for fav in favorite_players]
        player_data = player_dict["data"]
        return render_template(
            "/player_search.html", players=player_data, favorited_ids=favorited_ids
        )
    else:
        player_dict = name_search.model_dump()
        player_data = player_dict["data"]
        return render_template("/player_search.html", players=player_data)


@app.route("/<int:player_id>/player-stats")
def player_stats(player_id):
    try:
        stats = api.nba.stats.list(player_ids=[player_id], seasons=[2024])
        stats_dict = stats.model_dump()
        print(f"Stats data structure: {stats_dict}")
        game_stats = stats_dict["data"]
        season_stats = stats_dict["data"]
        ppg = round(sum(game["pts"] for game in season_stats) / len(season_stats), 1)
        rpg = round(sum(game["reb"] for game in season_stats) / len(season_stats), 1)
        apg = round(sum(game["ast"] for game in season_stats) / len(season_stats), 1)
        return render_template(
            "stats.html",
            games=game_stats,
            teams=teams,
            ppg=ppg,
            rpg=rpg,
            apg=apg,
        )
    except Exception as e:
        print(f"API Error: {str(e)}")
        flash("Error loading player stats.", "danger")
        return redirect("/")


@app.route("/<int:player_id>/bet-line-check", methods=["GET", "POST"])
def check_bet_line(player_id):
    form = LineCheckForm()
    try:
        stats = api.nba.stats.list(player_ids=[player_id], seasons=[2024])
        stats_dict = stats.model_dump()
        print(f"Stats data structure: {stats_dict}")
        game_stats = stats_dict["data"]
        season_stats = stats_dict["data"]
        stat_cat = form.stat_cat.data
        stat_reached = 0
        if form.validate_on_submit():
            bet_line = form.bet_line.data
            comp_bet_line = int(bet_line)
            if stat_cat == "points":
                for game in season_stats:
                    if game["pts"] > comp_bet_line:
                        stat_reached += 1

            elif stat_cat == "rebounds":
                for game in season_stats:
                    if game["reb"] > comp_bet_line:
                        stat_reached += 1

            elif stat_cat == "assists":
                for game in season_stats:
                    if game["ast"] > comp_bet_line:
                        stat_reached += 1

            return render_template(
                "stat_to_line_comp.html",
                games=game_stats,
                stat_reached=stat_reached,
                bet_line=bet_line,
            )
    except Exception as e:
        return jsonify({"error": str(e)})
    return render_template("bet_check.html", form=form)


@app.route("/users/add_favorite_player/<int:player_id>", methods=["GET", "POST"])
def favorite_players(player_id):
    if not g.user:
        flash(
            "You are not logged in.Please log in or create an account to get started!",
            "danger",
        )
        return redirect("/login")
    try:
        existing_favorite = favorite_player.query.filter_by(
            user_id=g.user.id, player_id=player_id
        ).first()
        if existing_favorite:
            flash("This Player is already favorited!", "warning")
            return redirect("/")
        else:
            new_player = favorite_player(player_id=player_id, user_id=g.user.id)
        db.session.add(new_player)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {str(e)}")
        flash("Error adding player to favorites.", "danger")


@app.route("/users/<int:player_id>/delete", methods=["GET", "POST"])
def remove_favorite(player_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        existing_favorite = favorite_player.query.filter_by(
            user_id=g.user.id, player_id=player_id
        ).first()
        if existing_favorite:
            db.session.delete(existing_favorite)
            db.session.commit()
            return redirect("/")

    return redirect("/")


@app.route("/logout")
def logout():
    if g.user:
        do_logout()
        return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
