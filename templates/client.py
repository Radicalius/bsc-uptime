import requests, time, hashlib

ping_interval = {{ping_interval}}

while True:
    requests.post("https://bscuptime.herokuapp.com/ping", json={"user": "{{user}}", "monitor": "{{monitor}}", "credentials": hashlib.sha256(("{{key}}"+"|"+str(int(time.time())//ping_interval)).encode("utf8")).hexdigest()})
    time.sleep(ping_interval)
