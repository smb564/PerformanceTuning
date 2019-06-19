import sklearn.gaussian_process as gp
import numpy as np
import random
from scipy.stats import norm
from skopt.acquisition import gaussian_ei
import time
import requests
import sys
import csv


def dummy_model(x):
    return 5*x[0]**2 - 4*x[1]*x[0] + 33 * x[1] + 334


def acquisition_function(x, model, minimum):
    x = np.array(x).reshape(1, -1)
    mu, sigma = model.predict(x, return_std=True)
    print(mu, sigma)
    with np.errstate(divide='ignore'):
        Z = (minimum - mu) / sigma
        print(norm.cdf(Z))
        expected_improvement = (minimum - mu) * norm.cdf(Z) + sigma * norm.pdf(Z)
        # expected_improvement[sigma == 0.0] = 0.0
    return -1 * expected_improvement


def normalize(x):
    if only_tomcat:
        assert len(x) == 3
        return [x[0] / KEEP_ALIVE_TIMEOUT_MAX, x[1] / MIN_SPARE_THREADS_MAX, x[2] / MAX_THREADS_MAX]
    assert len(x) == 6
    return [x[0] / MIN_SPARE_SERVERS_MAX, x[1] / MAX_SPARE_SERVERS_MAX, x[2] / MAX_REQUEST_WORKERS_MAX,
            x[3] / KEEP_ALIVE_TIMEOUT_MAX, x[4] / MIN_SPARE_THREADS_MAX, x[5] / MAX_THREADS_MAX]


def get_performance_only_tomcat(x, i):
    global data
    # [keep alive, min spare threads, max threads]
    prev_max_threads = int(requests.get("http://192.168.32.2:8080/getparam?name=maxThreads").json())

    requests.put("http://192.168.32.2:8080/setparam?name=keepAliveTimeout&value="+str(x[0]))

    if x[1] > prev_max_threads:
        requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(x[2]))
        requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(x[1]))
    else:
        requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(x[1]))
        requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(x[2]))

    time.sleep((i+1) * tuning_interval - time.time())

    res = requests.get("http://192.168.32.2:8080/performance?server=client").json()
    data.append(res)
    print("Mean response time : " + str(res[2]))
    return float(res[2])


folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
case_name = sys.argv[2]

ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
tuning_interval = int(sys.argv[6])

data = []
param_history = []
test_duration = ru + mi + rd
iterations = test_duration // tuning_interval

noise_level = 1e-8
initial_points = 5

# Apache parameters
# minSpareServers (5, 85) 5
# maxSpareServers (15, 95) 10
# maxRequestWorkers (50, 600) 256
# keepAliveTimeout (1, 21) 5

# Tomcat
# minSpareThreads (5, 85) 25
# maxThreads (50, 600) 200
MIN_SPARE_SERVERS_MAX = 85
MAX_SPARE_SERVERS_MAX = 95
MAX_REQUEST_WORKERS_MAX = 600
KEEP_ALIVE_TIMEOUT_MAX = 21
MIN_SPARE_THREADS_MAX = 85
MAX_THREADS_MAX = 600

only_tomcat = True

model = gp.GaussianProcessRegressor(kernel=gp.kernels.Matern(), alpha=noise_level,
                                    n_restarts_optimizer=10, normalize_y=True)

x_data = []
y_data = []

# let's measure the performance for the default config first and save it
x_data.append(normalize([5, 25, 200]))
y_data.append(get_performance_only_tomcat([5, 25, 200], 0))
param_history.append([5, 25, 200])

# sample more random (or predetermined data points) and collect numbers (up to initial points)
for i in range(1, initial_points):
    x1 = random.randint(1, 21)
    x2 = random.randint(5, 85)
    x3 = random.randint(max(50, x2), 600)

    x_data.append(normalize([x1, x2, x3]))
    y_data.append(get_performance_only_tomcat([x1, x2, x3], i))
    param_history.append([x1, x2, x3])

model.fit(x_data, y_data)

start_time = time.time()

# use bayesian optimization
for i in range(initial_points, iterations):
    minimum = min(y_data)
    max_expected_improvement = 0
    max_points = []
    max_points_unnormalized = []

    if only_tomcat:
        for keep_alive_timeout in range(1, KEEP_ALIVE_TIMEOUT_MAX + 1, 2):
            for min_spare_threads in range(5, MIN_SPARE_THREADS_MAX + 1, 5):
                for max_threads in range(max(50, min_spare_threads), MAX_THREADS_MAX + 1, 10):
                    x = [keep_alive_timeout, min_spare_threads, max_threads]
                    param_history.append(x)

                    x_normalized = normalize(x)
                    ei = gaussian_ei(np.array(x_normalized).reshape(1, -1), model, minimum)

                    if ei > max_expected_improvement:
                        max_expected_improvement = ei
                        max_points = [x_normalized]
                        max_points_unnormalized = [x]

                    elif ei == max_expected_improvement:
                        max_points.append(x_normalized)
                        max_points_unnormalized.append(x)
    else:
        for min_spare_servers in range(5, MIN_SPARE_SERVERS_MAX + 1, 5):
            for max_spare_servers in range(max(15, min_spare_servers + 1), MAX_SPARE_SERVERS_MAX + 1, 5):
                for max_request_workers in range(max(50, max_spare_servers), MAX_REQUEST_WORKERS_MAX + 1, 10):
                    for keep_alive_timeout in range(1, KEEP_ALIVE_TIMEOUT_MAX + 1, 2):
                        for min_spare_threads in range(5, MIN_SPARE_THREADS_MAX + 1, 5):
                            for max_threads in range(max(50, min_spare_threads), MAX_THREADS_MAX + 1, 10):
                                x = [min_spare_servers, max_spare_servers,max_request_workers,
                                     keep_alive_timeout, min_spare_threads, max_threads]

                                x_normalized = normalize(x)
                                ei = gaussian_ei(np.array(x_normalized).reshape(1, -1), model, minimum)

                                if ei > max_expected_improvement:
                                    max_expected_improvement = ei
                                    max_points = [x_normalized]

                                elif ei == max_expected_improvement:
                                    max_points.append(x_normalized)

    if max_expected_improvement == 0:
        print("WARN: Maximum expected improvement was 0. Most likely to pick a random point next")

    # select the point with maximum expected improvement
    # if there're multiple points with same ei, chose randomly
    idx = random.randint(0, len(max_points) - 1)
    next_x = max_points[idx]
    next_y = get_performance_only_tomcat(max_points_unnormalized[idx], i)
    x_data.append(next_x)
    y_data.append(next_y)

    model = gp.GaussianProcessRegressor(kernel=gp.kernels.Matern(), alpha=noise_level,
                                        n_restarts_optimizer=10, normalize_y=True)

    model.fit(x_data, y_data)

print("minimum found : ", min(y_data))

with open(folder_name + case_name + "/results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["IRR", "Request Count", "Mean Latency (for window)", "99th Latency"])
    for line in data:
        writer.writerow(line)

with open(folder_name + case_name + "/param_history.csv", "w") as f:
    writer = csv.writer(f)
    for line in param_history:
        writer.writerow(line)

