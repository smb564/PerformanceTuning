import requests
import time
from hyperopt import hp
from hyperopt import tpe
from hyperopt import Trials
from hyperopt import fmin
import csv

data = []
param_history = []
tuning_interval = 60  # in seconds

# query and get the current thread pool size (assuming fixed thread pool)
prev_param = int(requests.get("http://192.168.32.1:8080/getparam?name=minSpareThreads").json())


def objective(x):
    print("Setting fixed thread pool size to " + str(x))
    global prev_param
    # let's make this a fixed thread pool by maintaining minSpareThreads=maxThreads
    # we need make sure we set the params in correct order
    # (because we can't set a lower value for maxThreads than minSpareThreads)

    if int(x) > prev_param:
        requests.put("http://192.168.32.1:8080/setparam?name=maxThreads&value=" + str(int(x)))
        requests.put("http://192.168.32.1:8080/setparam?name=minSpareThreads&value=" + str(int(x)))
    else:
        requests.put("http://192.168.32.1:8080/setparam?name=minSpareThreads&value="+str(int(x)))
        requests.put("http://192.168.32.1:8080/setparam?name=maxThreads&value="+str(int(x)))

    prev_param = int(x)
    time.sleep(tuning_interval)
    res = requests.get("http://192.168.32.1:8080/performance").json()
    data.append(res)
    param_history.append(int(x))
    print("Mean response time : " + str(res[2]))
    return float(res[2])


space = hp.uniform('x', 20, 600)
tpe_trials = Trials()
tpe_best = fmin(fn=objective, space=space, algo=tpe.suggest, trials=tpe_trials, max_evals=12)


with open("tuner_results/results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["IRR", "Request Count", "Mean Latency (for window)", "99th Latency"])
    for line in data:
        writer.writerow(line)

with open("tuner_results/param_history.csv", "w") as f:
    writer = csv.writer(f)
    for line in param_history:
        writer.writerow([line])

print("Optimization complete")
#
# # requests.put("http://localhost:8080/setparam?name=maxThreads&value=" + str(50))
# # print(requests.get("http://localhost:8080/performance").json())