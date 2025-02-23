from flask import Flask, request, render_template, redirect, make_response
import psycopg2
import os
import json

from psycopg2.extras import Json
from psycopg2.extensions import register_adapter

register_adapter(dict, Json)

teams = json.load(open("config/teams.json"))

# Connect to the School database
conn = psycopg2.connect(
    dbname="tipping",
    user="postgres",
    password="tipping",
    host="tipping_db"
)
conn.autocommit = True
cursor = conn.cursor()


# Check for tables
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'users';")
if cursor.fetchone() is None:
    try:
        cursor.execute("CREATE TABLE users (username TEXT, password TEXT, name TEXT, flags TEXT[], children TEXT[])")
    except psycopg2.errors.DuplicateTable:
        pass

cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'rounds';")
if cursor.fetchone() is None:
    try:
        cursor.execute("CREATE TABLE rounds (id TEXT, name TEXT, start_date TEXT, end_date TEXT, matches TEXT[])")
    except psycopg2.errors.DuplicateTable:
        pass

# Create admin user
cursor.execute("SELECT * FROM users WHERE username='admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password, name, flags, children) VALUES ('admin', 'admin', 'Admin', ARRAY ['admin'], ARRAY []::text[])")

# DB Functions
def db_create_user(username, password, name, flags = [], children = []):
    cursor.execute("INSERT INTO users (username, password, name, flags, children) VALUES (%s, %s, %s, %s::text[], %s::text[])", (username, password, name, flags, children))

def db_create_round(id, name, start, end, matches):
    cursor.execute("INSERT INTO rounds (id, name, start_date, end_date, matches) VALUES (%s, %s, %s, %s, %s)", (id, name, start, end, matches))
    cursor.execute("CREATE TABLE %s (username TEXT, tips JSON[])" % id)

def db_submit_tips(round_id, username, tips):
    cursor.execute("INSERT INTO %s (username, tips) VALUES (%s, %s)" % (round_id, username, tips))

def postgres_list(list):
    postgres_list = "{"
    for item in list:
        postgres_list += item + ","
    postgres_list += "}"
    return postgres_list

TOKENS = {}

def auth(request):
    token = request.cookies.get('token')
    if token is None:
        return False
    try: username = TOKENS[token]
    except KeyError: return False
    return username

def get_user(username):
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    return user

app = Flask(__name__)


@app.route('/')
def index():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user is not None:
            token = os.urandom(16).hex()
            TOKENS[token] = username
            resp = make_response(redirect('/'))
            resp.set_cookie('token', token)
            return resp
    return render_template('login.html')

@app.route('/logout')
def logout():
    token = request.cookies.get('token')
    del TOKENS[token]
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route("/tips", methods=["GET", "POST"])
def tips():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)

    if request.method == "POST":
        tip = request.form["tip"]
        cursor.execute("INSERT INTO tips (username, tips) VALUES (%s, %s)", (user[0], tips))
    cursor.execute("SELECT * FROM tips")
    tips = cursor.fetchall()
    return render_template("tips.html", tips=tips, user=user)

@app.route("/admin")
def admin():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    if not "admin" in user[3]:
        return render_template('404.html')
    
    return render_template("admin.html", user=user)

@app.route("/admin/create_user", methods=["GET", "POST"])
def create_user():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    if not "admin" in user[3]:
        return render_template('404.html')

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        flags = request.form.getlist("flag")
        children = request.form.getlist("child")
        db_create_user(username, password, name, flags, children)
        return redirect("/admin/users")

    return render_template("create_user.html", user=user)

@app.route("/admin/users")
def users():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    if not "admin" in user[3]:
        return render_template('404.html')

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("users.html", users=users, user=user)

@app.route("/admin/users/<username>", methods = ["GET", "POST", "DELETE"])
def get_user_info(username):
    if request.method=="DELETE":
        cursor.execute("DELETE FROM users WHERE username=%s", (username,))
        return redirect("/admin/users")
    elif request.method=="POST":
        username=request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        flags = request.form.getlist("flag")
        children = request.form.getlist("child")
        cursor.execute("UPDATE users SET username=%s password=%s, name=%s, flags=%s::text[], children=%s::text[] WHERE username=%s", (username, password, name, flags, children))
        return redirect("/admin/users")
    else:
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        return render_template("user_info.html", user=user)

@app.route("/admin/create_round", methods=["GET", "POST"])
def create_round():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    if not "admin" in user[3]:
        return render_template('404.html')

    if request.method == "POST":
        round_id = request.form["round_id"]
        round_name = request.form["round_name"]
        start = request.form["start_date"]
        end = request.form["end_date"]
        matches = []

        for home, away, date in zip(request.form.getlist("home"), request.form.getlist("away"), request.form.getlist("match_date")):
            matches.append({"id":f"{home}v{away}", "home":home, "away":away, "date":date, "result":"tbd"})

        db_create_round(round_id, round_name, start, end, matches)
        return redirect("/admin/rounds")
        

    return render_template("create_round.html", user=user, teams = teams["teams"])

@app.route("/admin/rounds")
def rounds():
    user = auth(request)
    if user==False:
        return render_template('login.html')
    user = get_user(user)
    if not "admin" in user[3]:
        return render_template('404.html')

    cursor.execute("SELECT * FROM rounds")
    rounds = cursor.fetchall()
    return render_template("rounds.html", rounds=rounds, user=user)

@app.route("/admin/rounds/<roundid>", methods = ["GET", "POST", "DELETE"])
def get_round_info(roundid):
    if request.method=="DELETE":
        cursor.execute("DELETE FROM rounds WHERE id=%s", (roundid,))
        cursor.execute("DROP TABLE %s" % roundid)
        return redirect("/admin/rounds")

    elif request.method=="POST":
        round_name = request.form["name"]
        start = request.form["start"]
        end = request.form["end"]
        matches = []

        for home, away, date, result in zip(request.form.getlist("home"), request.form.getlist("away"), request.form.getlist("match_date"), request.form.getlist("result")):
            matches.append({"id":f"{home}v{away}", "home":home, "away":away, "date":date})

        cursor.execute("UPDATE rounds SET name=%s, start_date=%s, end_date=%s, WHERE id=%s", (round_name, start, end, roundid))
        return redirect("/admin/rounds")
    else:
        cursor.execute("SELECT * FROM rounds WHERE id=%s", (roundid,))
        round = list(cursor.fetchone())
        for match in round[4]:
            index = round[4].index(match)
            round[4][index] = json.loads(match)
        return render_template("round_info.html", round=round)



if __name__ == '__main__':
    app.run("0.0.0.0", 3000)
