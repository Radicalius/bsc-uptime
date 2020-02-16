import requests, time, hashlib

ping_interval = {{ping_interval}}

while True:
    try:
        requests.post("https://bscuptime.herokuapp.com/ping", json={"user": "{{user}}", "monitor": "{{monitor}}", "credentials": "{{key}}" })
    except:
        pass
    time.sleep(ping_interval)
