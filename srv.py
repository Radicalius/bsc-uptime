import sqlite3, time, sys, smtplib, ssl, _thread, datetime
import flask
import hashlib
from flask import Flask, request, render_template

app = Flask(__name__)
app.jinja_env.globals.update(datetime=datetime)

ping_interval = 30

def click():
    return int(time.time() // ping_interval)

def hash_key(key):
    return hashlib.sha256((key+"|"+str(click())).encode("utf8")).hexdigest()

@app.route("/")
def index():
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute("SELECT state, name, lastPing, up24h, up7d, up30d FROM monitors")
    data = curr.fetchall()
    return render_template("index.html", monitors=data)

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
    sender_email = "mr.zacharycotton@gmail.com"
    password = open("credentials").read()
    message = """\
    Subject: Monitor {0} is {1}

    Monitor {0} is {1}.""".format(monitor, state)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

def mailer():
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    while True:
        curr.execute("SELECT name, lastPing, email, state FROM monitors")
        for monitor in curr.fetchall():
            name, lastPing, email, state = monitor
            if (time.time() - lastPing > ping_interval and state):
                curr.execute("UPDATE monitors SET state = false WHERE name = ?", [name])
                send_email(email, name, "DOWN")
            if (time.time() - lastPing <= ping_interval and not state):
                curr.execute("UPDATE monitors SET state = true WHERE name = ?", [name])
                send_email(email, name, "UP")
        con.commit()
        time.sleep(ping_interval)

if __name__ == "__main__":

    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.executescript(open("schema.sql", "r").read())

    _thread.start_new(mailer, ())

    app.run(host="0.0.0.0", port="25522")
