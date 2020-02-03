import sqlite3, sys, time
import flask
import hashlib
from flask import Flask, request

app = Flask(__name__)

def hash_key(key):
    return hashlib.sha256((key+"|"+str(int(time.time())%300)).encode("utf8")).hexdigest()

@app.route("/ping/<monitor>", methods=["POST"])
def ping(monitor):
    con = sqlite3.connect("main.db")
    curr = con.cursor()
    try:
        curr.execute("SELECT key FROM monitors WHERE name = ?", [monitor])
        key = curr.fetchone()[0]
        print(key)
        if (request.get_json()["credentials"] == hashlib):
            return "", 201
        else:
            return "Unauthorized", 403
    except:
        print (sys.exc_info())
        return "Invalid Request", 400

if __name__ == "__main__":

    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.executescript(open("schema.sql", "r").read())

    app.run(host="0.0.0.0", port="25522")
