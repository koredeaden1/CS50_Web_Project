import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from datetime import datetime

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
db = SQL("sqlite:///data.db")

@app.route("/")
@login_required
def index():
    """Show current team built"""
    A = session["user_id"] #User ID
    rows = db.execute("SELECT * FROM team WHERE user_id = :user_id", user_id = A)
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = A)
    B = cash[0]['cash'] #User's available cash
    C = 0
    for row in rows:
        D = row['value']
        C += D #Collates Player Values

    return render_template("index.html", dic = rows, cash = B, total = C)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add cash to user"""
    if request.method == "POST":
        A = session["user_id"] #User ID
        B = db.execute("SELECT cash FROM users WHERE id = :user", user = A)
        C = B[0]['cash'] #User's initial cash
        D = request.form.get("add")
        if not D:
            return apology("invalid cash input", 403)
        E = int(D) #User's additional cash
        F = C + E #User's new cash

        #Update cash in users table
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = F, user_id = A)

        # Redirect user to home page
        flash('Cash Added!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")

@app.route("/buy")
@login_required
def bac():
    """Displays select menu in quote.html"""
    # Query database football positions
    Z = session["user_id"] #User ID
    A = db.execute("SELECT position FROM players GROUP BY position")
    B = []
    for row in A:
        B.append(row['position'])

    C = db.execute("SELECT position FROM team WHERE user_id = :id", id = Z)
    D = []
    for row in C:
        D.append(row['position'])

    E = [] #Positions not filled
    for i in B:
        if i not in D or i == "Centre-back":
            E.append(i)
    print(E)
    return render_template("buy.html", dic = E)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy football players"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        Z = session["user_id"] #User ID
        A = request.form.get("position")
        B = request.form.get("name")
        if not A or A == None:
            return apology("invalid player position", 403)
        else:
            C = f"%{ B }%"
            D = db.execute("SELECT * FROM players WHERE position = ? AND name LIKE ?", A, C)
            if not D:
                return apology("invalid player name", 403)
            elif len(D) != 1:
                return apology("player name needs to be more specific", 403)
        E = D[0] #Current player dictionary
        F = db.execute("SELECT * FROM team WHERE user_id = :id AND position = :pos", id = Z, pos = E['position'])
        if F:
            return apology("player position already filled")
        else:
            G = db.execute("SELECT cash FROM users WHERE id = :user", user = Z)
            H = G[0]['cash'] #User's initial cash
            I = int(E['value']) # Total Cost of transaction
            J = H - I #User's cash after transaction

            if J < 0:
                return apology("Not enough cash to purchase player", 403)

            L = datetime.now().strftime("%c") #Date of transaction

            #Inserting new transaction into history table
            db.execute("INSERT INTO history (user_id, player_name, price, position, time, type) VALUES(?, ?, ?, ?, ?, ?)",
                        Z, E['name'], I, E['position'], L, 'buy')
            #Update cash in users table
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = J, user_id = Z)
            #Insert players in team table
            db.execute("INSERT INTO team (user_id, name, position, value) VALUES(?, ?, ?, ?)", Z, E['name'], E['position'], I)

        # Redirect user to home page
        flash('Player Bought!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    A = session["user_id"] #User ID
    rows = db.execute("SELECT * FROM history WHERE user_id = :user_id", user_id = A)
    return render_template("history.html", dic = rows)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('You were successfully logged in')
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

@app.route("/quote")
@login_required
def qac():
    """Displays select menu in quote.html"""
    # Query database football positions
    rows = db.execute("SELECT position FROM players GROUP BY position")
    return render_template("quote.html", dic = rows)

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get player information for specified position"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        A = request.form.get("position")
        if not A:
            return apology("invalid football position", 403)
        else:
            B = db.execute("SELECT * FROM players WHERE position = :position", position = A)
            return render_template("quoted.html", dic = B)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted and not taken
        if not request.form.get("username"):
            return render_template("register.html", T = 1)
        else:
            A = db.execute("SELECT COUNT(id) AS n FROM users WHERE username = :name",
                            name=request.form.get("username"))
            if A[0]['n'] != 0:
                return render_template("register.html", T = 2)

        # Ensure password was properly typed and submitted
        if not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("register.html", T = 3)
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", T = 4)

        #Inserting new user into user table
        name = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", name, password)

        # Redirect user to home page
        flash('You were successfully registered')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", T = 0)

@app.route("/sell")
@login_required
def sac():
    """Updates select menu in sell.html"""
    A = session["user_id"] #User ID
    # Query database for players
    rows = db.execute("SELECT name FROM team WHERE user_id = :user_id", user_id = A)
    return render_template("sell.html", dic = rows)

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell football players"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        Z = session["user_id"] #User ID
        A = request.form.get("name")
        if not A or A == None:
            return apology("invalid player", 403)
        else:
            B = db.execute("SELECT * FROM team WHERE user_id = :id", id = Z)
            C = B[0] #Current player dictionary
            D = db.execute("SELECT cash FROM users WHERE id = :user", user = Z)
            E = D[0]['cash'] #User's initial cash
            F = C['value'] # Total transaction gain
            G = E + F #User's cash after transaction

            H = datetime.now().strftime("%c") #Date of transaction

            #Inserting new transaction into history table
            db.execute("INSERT INTO history (user_id, player_name, price, position, time, type) VALUES(?, ?, ?, ?, ?, ?)",
                        Z, A, F, C['position'], H, 'sell')
            #Update cash in users table
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = G, user_id = Z)
            #Update players in team table
            print(Z)
            print(A)
            db.execute("DELETE FROM team WHERE user_id = ? AND name = ?", Z, A)

            # Redirect user to home page
            flash('Player Sold!')
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")

@app.route("/images")
@login_required
def img():
    """Displays football carousel"""
    return render_template("img.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

#Python Run
if __name__ == '__main__':
    app.run(debug=True)