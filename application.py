import os, re, requests, random

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///vocab.db")

@app.route("/")
@login_required
def index():
    """Show user's flashcard sets"""

    folders = db.execute("SELECT * from folders WHERE user_id = ?", session["user_id"])
    user = db.execute("SELECT name from users WHERE id = ?", session["user_id"])
    return render_template("index.html", folders=folders, user=user)


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Delete folders"""
    for elm in ["words","folders","definitions"]:
        db.execute("DELETE FROM ? WHERE folder_id = ?", elm, request.form.get("folder_id"))
    flash('Set removed!')
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["folder_id"] = 0

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        name = request.form.get("name")
        password = request.form.get("password")
        if password != request.form.get("confirmation"):
            return apology("passwords do not match")
        # Validate password: check for a combination of letters (at least one of which is capitalized),
        # digits, and special characters
        elif len(db.execute("SELECT * from users WHERE username = ?", username)) == 1:
            return apology("username already exists")
        elif len(password) < 8:
            return apology("Password must be at least 8 characters long")
        else:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (name, username, hash) VALUES (?, ?, ?)", name, username, hash)
            rows = db.execute("SELECT id from users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]
            session["folder_id"] = 0
            flash('Registered!')
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/new-set", methods=["GET", "POST"])
@login_required
def create_set():
    """Creates a new folder"""

    if request.method == "POST":
        folder = request.form.get("folder")
        db.execute("INSERT INTO folders (user_id, folder) VALUES (?, ?)", session["user_id"], folder)
        flash('Set created!')
        return redirect("/")
    return render_template("folder.html")


@app.route("/new-flashcard")
@login_required
def create_flashcard():
    """Select the destination folder and add content to flashcard"""

    folder_id = session["folder_id"]
    session["folder_id"] = 0
    rows = db.execute("SELECT * from folders WHERE user_id = ?", session["user_id"])
    return render_template("flashcard.html", rows=rows, folder_id=folder_id)


@app.route("/new-flashcard/add-definitions", methods=["POST"])
@login_required
def add_defs():
    """Look up the term and return user a list of definitions"""

    folder_id = request.form.get("folder_id")
    word = request.form.get("word")
    if not lookup(word):
        return apology("No result found")
    return render_template("definitions.html", definitions=lookup(word), folder_id=folder_id, word=word)


@app.route("/submit-flashcard", methods=["POST"])
@login_required
def submit():
    """Insert new card into the database"""

    # The name of the input are the same for both options
    definitions = request.form.getlist("definition")
    folder_id = request.form.get("folder_id")
    word = request.form.get("word")
    # Add a new entry to "words" table => obtain the word_id which we will use to register definitions into the definition table
    db.execute("INSERT INTO words (folder_id, word, user_id) VALUES (?, ?, ?)", folder_id, word, session["user_id"])
    # Update number of terms inside the set
    row = db.execute("SELECT word_count from folders WHERE folder_id = ?", folder_id)
    db.execute("UPDATE folders SET word_count = ? WHERE folder_id = ?", int(row[0]["word_count"]) + 1, folder_id)
    # Pull from database the latest word added to the selected folder
    row = db.execute("SELECT MAX(word_id) as word_id from words WHERE folder_id = ?", folder_id)
    # If user manually typed the definitions, make sure line breaks in the definitions are preserved before inserting into the table
    # If user looked up the definitions, insert definitions straight into the database
    for d in definitions:
        # Add a new entry to "definitions" table
        # \n doesn't work in HTML, convert them to <br> and use safe filter when parsing string to template
        if request.form.get("button") == "Create":
            d = d.replace('\n', '<br>')
        db.execute("INSERT INTO definitions (word_id, definition, user_id, folder_id) VALUES (?, ?, ?, ?)", row[0]["word_id"], d, session["user_id"], folder_id)
    flash("Flashcard created!")
    # Update folder_id to the id of the last selected folder
    session["folder_id"] = folder_id
    # Return to the create flashcard page, make sure it remembers the last selected folder by passing an additional parameter
    return redirect("/new-flashcard")


@app.route("/view", methods=["POST"])
@login_required
def view():
    """Review flashcards"""

    cards = []
    entry = {}
    # Pull from database words that are inside the selected folder
    words = db.execute("SELECT * from words WHERE folder_id = ?", request.form.get("folder_id"))
    rows = db.execute("SELECT * from folders WHERE user_id = ?", session["user_id"])
    # For each word, get its definitions from the database
    for w in words:
        # Create flashcards from the data we pull from the database. Append the cards to the cards array
        # Each card is a dictionary with two key/value pairs.
        # Value of the definitions key is a list of definition pulled from the definition table given the id of the term
        entry["word"] = w["word"]
        entry["definitions"] = [row["definition"] for row in db.execute("SELECT definition from definitions WHERE word_id = ?", w["word_id"])]
        cards.append(entry.copy())
    if request.form.get("button") == "Shuffle!":
        random.shuffle(cards)
    return render_template("view.html", cards=cards, folder_id=request.form.get("folder_id"), rows=rows)


@app.route("/edit", methods=["POST"])
@login_required
def edit():
    """Make any changes to a flashcard set as needed"""

    cards = []
    entry = {}
    # Pull from database name of the selected set and all the terms inside it
    words = db.execute("SELECT * from words WHERE folder_id = ?", request.form.get("folder_id"))
    folder = db.execute("SELECT folder from folders WHERE folder_id = ?", request.form.get("folder_id"))
    # For each term that was pulled from the 'words' table, go get its definitions from the corresponding table
    # Create entries with four key/value pairs and append to the cards list
    for w in words:
        entry["word_id"] = w["word_id"]
        entry["word"] = w["word"]
        # the two following keys have their value as a list
        entry["definitions"] = [row["definition"] for row in db.execute("SELECT definition from definitions WHERE word_id = ?", w["word_id"])]
        entry["def_id"] = [row["def_id"] for row in db.execute("SELECT def_id from definitions WHERE word_id = ?", w["word_id"])]
        cards.append(entry.copy())
    return render_template("edit.html", cards=cards, folder_id=request.form.get("folder_id"), folder=folder[0]["folder"])


@app.route("/edit/finish", methods=["POST"])
@login_required
def edit_finish():
    """Make changes requested by user"""

    # Get submitted data
    folder_id = request.form.get("folder_id")
    new_folder =  request.form.get("new_folder")
    word = request.form.getlist("word")
    word_id = [int(e) for e in request.form.getlist("word_id")]
    definition = request.form.getlist("definition")
    def_id = [int(e) for e in request.form.getlist("def_id")]
    delete_id = request.form.getlist("delete_id")
    # Rename folder
    if request.form.get("new_folder") != "":
        new_folder = new_folder.removesuffix("<br>")
        db.execute("UPDATE folders SET folder = ? WHERE folder_id = ?", new_folder, folder_id)
    # Delete terms, update the SQL query each time a term is deleted
    for i in delete_id:
        row = db.execute("SELECT word_count from folders WHERE folder_id = ?", folder_id)
        db.execute("DELETE FROM words WHERE word_id = ?", i)
        db.execute("DELETE FROM definitions WHERE word_id = ?", i)
        db.execute("UPDATE folders SET word_count = ? WHERE folder_id = ?", int(row[0]["word_count"]) - 1, folder_id)
    # Edit terms and definitions (excluding the ones that have been deleted)
    # Data pulled from SQL including numbers are of string type, so make sure to convert the id to integer
    word_id_list = [int(row["word_id"]) for row in db.execute("SELECT word_id from words WHERE folder_id = ?", folder_id)]
    for i in range(len(word_id)):
        if word_id[i] in word_id_list and word[i] != "":
            word[i] = word[i].removesuffix("<br>")
            db.execute("UPDATE words SET word = ? WHERE word_id = ?", word[i], word_id[i])
    def_id_list = [int(row["def_id"]) for row in db.execute("SELECT def_id from definitions WHERE folder_id = ?", folder_id)]
    for i in range(len(def_id)):
        if def_id[i] in def_id_list and definition[i] != "":
            definition[i] = definition[i].removesuffix("<br>")
            db.execute("UPDATE definitions SET definition = ? WHERE def_id = ?", definition[i], def_id[i])
    return redirect("/")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def password():
    """Change user's password"""

    if request.method == "POST":
        current_pass = request.form.get("current_pass")
        new_pass = request.form.get("new_pass")
        rows = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        if not check_password_hash(rows[0]["hash"], current_pass):
            return apology("Current password doesn't match our record")
        if new_pass != request.form.get("confirmation"):
            return apology("Please verify your password")
        elif len(new_pass) < 8:
            return apology("Password must be at least 8 characters long")
        else:
            hash = generate_password_hash(new_pass)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])
            flash('Password updated')
            return redirect("/")
    else:
        return render_template("password.html")


def errorhandler(e):
    """Handle error"""

    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
