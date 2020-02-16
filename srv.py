import sqlite3, time, sys, smtplib, ssl, _thread, datetime, random, string, random, os
import flask
import hashlib
from flask import Flask, request, render_template, redirect, make_response, flash
from email.message import EmailMessage
import psycopg2
import urllib.parse as urlparse

def perc(a,b):
    if (a + b == 0):
        return 0
    return (a / (a+b)) * 100

def big_perc(a,b):
    if (a + b == 0):
        return 0
    return (a / (a+b)) * 100 + (b/(a+b)) * 100

app = Flask(__name__)
app.jinja_env.globals.update(datetime=datetime,perc=perc,big_perc=big_perc)
ping_interval = 60

def click():
    return int(time.time() // ping_interval)

def hash_key(key):
    return hashlib.sha256((key+"|"+str(click())).encode("utf8")).hexdigest()

def rand():
    chars = string.ascii_lowercase
    return ''.join(random.choice(chars) for x in range(32))

app.secret_key = rand()

def validate(sessionId, curr):
    if not sessionId:
        return None
    curr.execute("SELECT name FROM sessions WHERE id = %s", [sessionId])
    users = curr.fetchall()
    if not users:
        return None
    else:
        return users[0][0]

@app.route("/login", methods=["GET", "POST"])
def login():
    con = connect()
    curr = con.cursor()
    if request.method == "GET":
        return render_template("login.html")
    else:
        try:
            curr.execute("SELECT password FROM users WHERE name = %s", [request.form["email"]])
            hash = curr.fetchone()[0]
            if hash == request.form["password"]:
                sessionId = rand()
                curr.execute("INSERT INTO sessions VALUES (%s, %s)", [sessionId, request.form["email"]])
                con.commit()
                resp = make_response(redirect("/"))
                resp.set_cookie("sessionId", sessionId)
                return resp
            else:
                flash("Invalid Credentials")
                return render_template("login.html")
        except:
            flash("Invalid Credentials")
            return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute("DELETE FROM sessions WHERE name = %s", [user])
    con.commit()
    return redirect("/login")

@app.route("/")
def index():
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    rand = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
    curr.execute("SELECT state, name, lastPing, up24h, down24h, up7d, down7d, up30d, down30d FROM monitors WHERE user_ = %s", [user])
    data = curr.fetchall()
    return render_template("index.html", monitors=data, rand=rand, user=user)

@app.route("/add", methods=["POST"])
def add():
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute('INSERT INTO monitors VALUES (%s, %s, %s, %s, 0,0,0,0,0,0,0,true)', [request.form["name"], request.form["key"], user, request.form["contacts"]])
    con.commit()
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete():
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute("DELETE FROM monitors WHERE name = %s AND user_ = %s", [request.form["name"], user])
    con.commit()
    return redirect("/")

@app.route("/edit", methods=["POST"])
def edit():
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute('UPDATE monitors SET key = %s, email = %s WHERE name = %s AND user_ = %s', [request.form["key"], request.form["contacts"], request.form["name"], user])
    con.commit()
    return redirect("/")

@app.route("/monitor/<monitor>")
def monitor(monitor):
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute("SELECT name, key, email FROM monitors WHERE name = %s AND user_ = %s", [monitor, user])
    return "|".join(curr.fetchone())

@app.route("/client/<monitor>")
def client(monitor):
    con = connect()
    curr = con.cursor()
    user = validate(request.cookies.get("sessionId"), curr)
    if not user:
        return redirect("/login")
    curr.execute("SELECT key FROM monitors WHERE name = %s AND user_ = %s", [monitor, user])
    key = curr.fetchone()[0]
    return render_template("client.py", key=key, monitor=monitor, ping_interval=ping_interval / 3, user=user)

@app.route("/ping", methods=["POST"])
def ping():
    con = connect()
    curr = con.cursor()
    try:
        curr.execute("SELECT key FROM monitors WHERE user_ = %s AND name = %s", [request.get_json()["user"], request.get_json()["monitor"]])
        key = curr.fetchone()[0]
        print(key)
        if (request.get_json()["credentials"] == hash_key(key)):
            curr.execute("UPDATE monitors SET lastPing = %s, up24h = up24h+1, up7d = up7d+1, up30d=up30d+1 WHERE user_ = %s AND name = %s", [int(time.time()), request.get_json()["user"], request.get_json()["monitor"]])
            con.commit()
            return "", 201
        else:
            return "Unauthorized", 403
    except:
        raise Exception(sys.exc_info())
        return "Invalid Request", 400


def send_email(receiver_email, monitor, state):
    port = 465
    smtp_server = "smtp.gmail.com"
    sender_email = "bscuptime@gmail.com"
    password = email_password
    message = EmailMessage()
    message["From"] = "bscuptime@gmail.com"
    message["To"] = receiver_email
    message["Subject"] = "Monitor {0} is {1}".format(monitor, state)
    message.set_content("Monitor {0} is {1}".format(monitor, state))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.send_message(message)

def mailer():
    con = connect()
    curr = con.cursor()
    while True:
        curr.execute("SELECT name, lastPing, email, state FROM monitors")
        for monitor in curr.fetchall():
            name, lastPing, email, state = monitor
            if (time.time() - lastPing > ping_interval and state):
                curr.execute("UPDATE monitors SET state = false WHERE name = %s", [name])
                for i in str(email).split(","):
                    send_email(i.strip(), name, "DOWN")
            if (time.time() - lastPing <= ping_interval and not state):
                curr.execute("UPDATE monitors SET state = true WHERE name = %s", [name])
                for i in str(email).split(","):
                    send_email(i.strip(), name, "UP")
            if (not state):
                curr.execute("UPDATE monitors SET down24h = down24h+1, down7d = down7d+1, down30d=down30d+1 WHERE name = %s", [name])
        con.commit()
        time.sleep(ping_interval)

def connect():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    return psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
            )

con = connect()
curr = con.cursor()
curr.execute(open("schema.sql", "r").read())
con.commit()

curr.execute("SELECT value FROM credentials WHERE key = 'email'")
email_password = curr.fetchall()[0][0]

_thread.start_new(mailer, ())
