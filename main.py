from flask import Flask, request, render_template, redirect
import psycopg2
import os

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
    cursor.execute("CREATE TABLE users (username TEXT, password TEXT, name TEXT, flags TEXT[], children TEXT[])")

cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'rounds';")
if cursor.fetchone() is None:
    cursor.execute("CREATE TABLE rounds (id TEXT, name TEXT, start_date TEXT, end_date TEXT, matches JSON[])")

# Create admin user
cursor.execute("SELECT * FROM users WHERE username='admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password, name, flags, children) VALUES ('admin', 'admin', 'Admin' ['admin'], [])")

# DB Functions
def create_user(username, password, name, flags = [], children = []):
    cursor.execute("INSERT INTO users (username, password, name, flags, children) VALUES (%s, %s, %s, %s, %s)", (username, password, name, flags, children))

def create_round(id, name, start, end, matches):
    cursor.execute("INSERT INTO rounds (id, name, start, end, matches) VALUES (%s, %s, %s, %s, %s)", (id, name, start, end, matches))
    cursor.execute("CREATE TABLE %s (username TEXT, tips JSON[])" % id)

def submit_tips(round_id, username, tips):
    cursor.execute("INSERT INTO %s (username, tips) VALUES (%s, %s)" % (round_id, username, tips))


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
            return redirect('/', set_cookie=('token', token))
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
        create_user(username, password, name, flags, children)
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

        for name, home, away, date in zip(request.form.getlist("match_name"), request.form.getlist("home"), request.form.getlist("away"), request.form.getlist("match_date")):
            matches.append({"id":f"{home}v{away}","name":name, "home":home, "away":away, "date":date})

        create_round(round_id, round_name, start, end, matches)
        return redirect("/admin/rounds")
        

    return render_template("create_round.html", user=user)

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


if __name__ == '__main__':
    app.run("0.0.0.0", 3000)
