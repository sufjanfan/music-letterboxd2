from cs50 import SQL
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
import requests

# Configure Flask app
app = Flask(__name__)


# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
db = SQL("sqlite:///songs.db")

# Homepage
@app.route("/")
def index():
    return render_template("index.html")

'''
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
'''

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return apology("must provide username and password")

        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(user) != 1 or not check_password_hash(user[0]["hash"], password):
            return apology("invalid username or password")

        session["user_id"] = user[0]["id"]
        return redirect("/profile")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # get form data using post method
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # makes sure fields/data category exist
        if not username:
            return apology("must provide username")
        if not password:
            return apology("must provide password")
        if not confirmation:
            return apology("must provide confirmation")
        # makes sure password and confirmation match
        if password != confirmation:
            return apology("passwords do not match")
        # hashes password so that actual password is not submitted
        # inserts user into database
        try:
            hash_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_password)
        except ValueError:
            return apology("username already exists")
        return redirect("/login")
    # go to registration page/form for GET requests
    else:
        return render_template("register.html")


'''
# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("must fill all fields")
        if password != confirmation:
            return apology("passwords do not match")

        hash_pwd = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_pwd)
        except:
            return apology("username already exists")

        return redirect("/login")

    return render_template("register.html")
    '''

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Profile
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        query = request.form.get("query")
        response = requests.get(f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json")
        if response.status_code != 200:
            return apology("MusicBrainz API error")

        songs = response.json().get("recordings", [])
        return render_template("profile.html", songs=songs)

    reviews = db.execute("SELECT * FROM reviews WHERE user_id = ?", session["user_id"])
    return render_template("profile.html", reviews=reviews)

# Add Review
@app.route("/review", methods=["POST"])
@login_required
def review():
    song_title = request.form.get("title")
    review_text = request.form.get("review")
    rating = request.form.get("rating")

    if not song_title or not review_text or not rating:
        return apology("must fill all fields")

    db.execute(
        "INSERT INTO reviews (user_id, title, review, rating) VALUES (?, ?, ?, ?)",
        session["user_id"], song_title, review_text, rating
    )
    return redirect("/profile")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get("query")
        if not query:
            return apology("must provide a search term")

        # Query the database for songs matching the search
        songs = db.execute(
            "SELECT id, title, artist FROM songs WHERE title LIKE ? OR artist LIKE ?",
            f"%{query}%", f"%{query}%"
        )

        return render_template("search.html", songs=songs)

    return render_template("search.html")


@app.route("/song/<song_id>")
def song_details(song_id):
    # Fetch song details (from external API or local database)
    response = requests.get(f"https://musicbrainz.org/ws/2/recording/{song_id}?fmt=json")
    if response.status_code != 200:
        return apology("MusicBrainz API error")

    song = response.json()
    # Fetch reviews from the database
    reviews = db.execute("SELECT reviews.*, users.username FROM reviews JOIN users ON reviews.user_id = users.id WHERE song_id = ?", song_id)

    # Calculate average rating
    ratings = [review["rating"] for review in reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else None

    return render_template("song.html", song=song, reviews=reviews, average_rating=average_rating)

@app.route("/song/<song_id>/review", methods=["POST"])
@login_required
def add_review(song_id):
    title = request.form.get("title")
    review_text = request.form.get("review")
    rating = request.form.get("rating")

    if not title or not review_text or not rating:
        return apology("must fill all fields")

    db.execute(
        "INSERT INTO reviews (user_id, song_id, title, review, rating) VALUES (?, ?, ?, ?, ?)",
        session["user_id"], song_id, title, review_text, rating
    )
    return redirect(f"/song/{song_id}")


if __name__ == "__main__":
    app.run(debug=True)
