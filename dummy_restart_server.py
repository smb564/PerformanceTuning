import requests
import time
import sys
import os

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
case_name = sys.argv[2]

ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
tune_interval = int(sys.argv[6])

data = []
param_history = []
test_duration = ru + mi + rd
tuning_interval = tune_interval  # in seconds
num_iter = test_duration // tuning_interval

for i in range(num_iter):
    requests.get("http://192.168.32.10:5001/reload")
    time.sleep(tuning_interval)
