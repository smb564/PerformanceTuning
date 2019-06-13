import requests
import time

# assuming it starts with the correct workload
time.sleep(1200)

requests.get("http://192.168.32.2:8080/changeEBCount?count=150")
time.sleep(600)

requests.get("http://192.168.32.2:8080/changeMix?mix=3&count=30")
time.sleep(600)

requests.get("http://192.168.32.2:8080/changeMix?mix=2&count=100")
requests.get("http://192.168.32.2:8080/changeThinkTime?scale=1")
time.sleep(600)

requests.get("http://192.168.32.2:8080/changeThinkTime?scale=0.1")
time.sleep(300)

requests.get("http://192.168.32.2:8080/changeThinkTime?scale=0.05")
