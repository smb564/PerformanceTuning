import requests
import time
from hyperopt import hp
from hyperopt import tpe
from hyperopt import Trials
from hyperopt import fmin
import csv
import sys
import os

#TODO : I REMOVED TUNING TOMCAT PARAMS!!!

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
case_name = sys.argv[2]

try:
    os.makedirs(folder_name+case_name)
except FileExistsError:
    print("directory already exists")

ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
tune_interval = int(sys.argv[6])

data = []
param_history = []
test_duration = ru + mi + rd
tuning_interval = tune_interval  # in seconds

# query and get the current thread pool size (assuming fixed thread pool)
prev_param = int(requests.get("http://192.168.32.2:8080/getparam?name=minSpareThreads").json())


def objective(x):
    print("Setting fixed thread pool size to " + str(x))
    global prev_param
    # let's make this a fixed thread pool by maintaining minSpareThreads=maxThreads
    # we need make sure we set the params in correct order
    # (because we can't set a lower value for maxThreads than minSpareThreads)

    if int(x) > prev_param:
        requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(int(x)))
        requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(int(x)))
    else:
        requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value="+str(int(x)))
        requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value="+str(int(x)))

    # set the MaxRequestWorkers of Apache webserver to the same value
    requests.get("http://192.168.32.10:5001/setParam?MaxRequestWorkers=" + str(int(x)))

    prev_param = int(x)
    time.sleep(tuning_interval)
    res = requests.get("http://192.168.32.2:8080/performance?server=apache").json()
    data.append(res)
    param_history.append(int(x))
    print("Mean response time : " + str(res[2]))
    return float(res[2])


space = hp.uniform('x', 20, 600)
tpe_trials = Trials()
tpe_best = fmin(fn=objective, space=space, algo=tpe.suggest, trials=tpe_trials, max_evals=test_duration//tuning_interval)


with open(folder_name + case_name + "/results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["IRR", "Request Count", "Mean Latency (for window)", "99th Latency"])
    for line in data:
        writer.writerow(line)

with open(folder_name + case_name + "/param_history.csv", "w") as f:
    writer = csv.writer(f)
    for line in param_history:
        writer.writerow([line])

print("Optimization complete")
