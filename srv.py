import sqlite3, time, sys, smtplib, ssl, _thread, datetime, random, string
import flask
import hashlib
from flask import Flask, request, render_template, redirect
from email.message import EmailMessage

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

ping_interval = 30

def click():
    return int(time.time() // ping_interval)

def hash_key(key):
    return hashlib.sha256((key+"|"+str(click())).encode("utf8")).hexdigest()

@app.route("/")
def index():
    rand = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute("SELECT state, name, lastPing, up24h, down24h, up7d, down7d, up30d, down30d FROM monitors")
    data = curr.fetchall()
    return render_template("index.html", monitors=data, rand=rand)

@app.route("/add", methods=["POST"])
def add():
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute('INSERT INTO monitors VALUES (?, ?, ?, 0,0,0,0,0,0,0,1)', [request.form["name"], request.form["key"], request.form["contacts"]])
    con.commit()
    return redirect("/")

@app.route("/edit", methods=["POST"])
def edit():
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute('UPDATE monitors SET key = ?, email = ? WHERE name = ?', [request.form["key"], request.form["contacts"], request.form["name"]])
    con.commit()
    return redirect("/")

@app.route("/monitor/<monitor>")
def monitor(monitor):
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute("SELECT name, key, email FROM monitors WHERE name = ?", [monitor])
    return "|".join(curr.fetchone())

@app.route("/client/<monitor>")
def client(monitor):
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute("SELECT key FROM monitors WHERE name = ?", [monitor])
    key = curr.fetchone()[0]
    return render_template("client.py", key=key, monitor=monitor, ping_interval=ping_interval)

@app.route("/ping/<monitor>", methods=["POST"])
def ping(monitor):
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    try:
        curr.execute("SELECT key FROM monitors WHERE name = ?", [monitor])
        key = curr.fetchone()[0]
        print(key)
        if (request.get_json()["credentials"] == hash_key(key)):
            curr.execute("UPDATE monitors SET lastPing = ?, up24h = up24h+1, up7d = up7d+1, up30d=up30d+1", [int(time.time())])
            con.commit()
            return "", 201
        else:
            return "Unauthorized", 403
    except:
        print(sys.exc_info())
        return "Invalid Request", 400


def send_email(receiver_email, monitor, state):
    port = 465
    smtp_server = "smtp.gmail.com"
    sender_email = "bscuptime@gmail.com"
    password = open("credentials").read()
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
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    while True:
        curr.execute("SELECT name, lastPing, email, state FROM monitors")
        for monitor in curr.fetchall():
            name, lastPing, email, state = monitor
            if (time.time() - lastPing > ping_interval and state):
                curr.execute("UPDATE monitors SET state = 0 WHERE name = ?", [name])
                for i in str(email).split(","):
                    send_email(i.strip(), name, "DOWN")
            if (time.time() - lastPing <= ping_interval and not state):
                curr.execute("UPDATE monitors SET state = 1 WHERE name = ?", [name])
                for i in str(email).split(","):
                    send_email(i.strip(), name, "UP")
            if (not state):
                curr.execute("UPDATE monitors SET down24h = down24h+1, down7d = down7d+1, down30d=down30d+1 WHERE name = ?", [name])
        con.commit()
        time.sleep(ping_interval)

con = sqlite3.connect("main.db")
curr = con.cursor()
curr.executescript(open("schema.sql", "r").read())

_thread.start_new(mailer, ())
