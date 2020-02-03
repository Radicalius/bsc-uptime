import sqlite3
import flask
from flask import Flask

app = Flask(__name__)

@app.route("/ping/<monitor>", methods=["POST"])
def ping(monitor):
    print(monitor)
    return ""

if __name__ == "__main__":

    con = sqlite3.connect("main.db")
    curr = con.cursor()
    curr.execute(open("schema.sql", "r").read())

    app.run(host="0.0.0.0", port="25522")
