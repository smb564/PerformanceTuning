# import random
# from skopt import gp_minimize
#
# count = 0
#
# def dummy_model(x):
#     global count
#     print("here")
#     count += 1
#     '''This is just to debug the code. This function cannot be minimized.'''
#     return x[0] * random.random() + x[1] * random.random()
#
#
# iterations = 10
# initial_points = 5
#
# max_clients_range = (20, 600)
# tomcat_threads_range = (20, 600)
#
# res = gp_minimize(func=dummy_model, dimensions=[max_clients_range, tomcat_threads_range],
#                   n_random_starts=initial_points, n_calls=iterations)
#
# print(count)
# print(len(res.models))


import requests
import time
import csv
import sys
import os
from skopt import gp_minimize

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
case_name = sys.argv[2]
only_tomcat = False

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
init_points = 8  # number of points to explore randomly initially
num_iter = test_duration // tuning_interval


# query and get the current thread pool size (assuming fixed thread pool)
prev_param = int(requests.get("http://192.168.32.2:8080/getparam?name=minSpareThreads").json())


def objective(p):
    x = p[0]
    y = p[1]
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
    requests.get("http://192.168.32.10:5001/setParam?MaxRequestWorkers=" + str(int(y)))

    prev_param = int(x)
    time.sleep(tuning_interval)
    res = requests.get("http://192.168.32.2:8080/performance?server=client").json()
    data.append(res)
    param_history.append([int(x), int(y)])
    print("Mean response time : " + str(res[2]))
    return float(res[2])


def objective_only_tomcat(x):
    x = x[0]
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

    prev_param = int(x)
    time.sleep(tuning_interval)
    res = requests.get("http://192.168.32.2:8080/performance?server=client").json()
    data.append(res)
    param_history.append([int(x)])
    print("Mean response time : " + str(res[2]))
    return float(res[2])


max_clients_range = (20, 600)
tomcat_threads_range = (20, 600)

if only_tomcat:
    res = gp_minimize(func=objective_only_tomcat, dimensions=[tomcat_threads_range], acq_func='EI',
                      n_random_starts=init_points, n_calls=num_iter)
else:
    res = gp_minimize(func=objective, dimensions=[max_clients_range, tomcat_threads_range],
                      n_random_starts=init_points, n_calls=num_iter, noise=1.0)


with open(folder_name + case_name + "/results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["IRR", "Request Count", "Mean Latency (for window)", "99th Latency"])
    for line in data:
        writer.writerow(line)

with open(folder_name + case_name + "/param_history.csv", "w") as f:
    writer = csv.writer(f)
    for line in param_history:
        writer.writerow(line)

# save the res object
import pickle

with open(folder_name + case_name + "/res.pickle", "wb") as f:
    pickle.dump(res, f)

print("Optimization complete")
