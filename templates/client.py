import requests, time, hashlib

ping_interval = {{ping_interval}}

while True:
    try:
        requests.post("https://bscuptime.herokuapp.com/ping", json={"user": "{{user}}", "monitor": "{{monitor}}", "credentials": hashlib.sha256(("{{key}}"+"|"+str(int(time.time())//ping_interval)).encode("utf8")).hexdigest()})
    except:
        pass
    time.sleep(ping_interval)
