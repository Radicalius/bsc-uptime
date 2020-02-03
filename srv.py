import sqlite3, time, sys
import flask
import hashlib
from flask import Flask, request

app = Flask(__name__)

ping_interval = 300

def click():
    return int(time.time() // ping_interval)

def hash_key(key):
    return hashlib.sha256((key+"|"+str(click())).encode("utf8")).hexdigest()

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

if __name__ == "__main__":

    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.executescript(open("schema.sql", "r").read())

    app.run(host="0.0.0.0", port="25522")
