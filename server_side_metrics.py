import requests
import matplotlib.pyplot as plt
import time
import csv

throughput = []
mean_latency = []

out_filename = "server_metrics/test_data.txt"

# duration in seconds
duration = 720
# interval in seconds
interval = 20

# calculate the iterations from duration/interval
iterations = int(duration/interval)

tuning_interval = 60  # in seconds (from bayesian_opt.py), -1 if not tuning


# server is returning total request count

prev = requests.get("http://192.168.32.1:8080/performance").json()[1]

for _ in range(iterations):
    # server records results (mean latency, 99 latency etc.) for 1 minute windows
    # (we can configure window inteval in tomcat/webapps/tpc-w/WEB-INF/web.xml file)
    time.sleep(interval)
    res = requests.get("http://192.168.32.1:8080/performance").json()
    throughput.append(float(res[1] - prev)/interval)
    prev = res[1]
    mean_latency.append(res[2])

# save the data\
with open(out_filename, "w") as f:
    writer = csv.writer(f)
    writer.writerows([["throughput"] + throughput, ["latency"] + mean_latency])

if tuning_interval != -1:
    tune_locations = [x*60.0/interval for x in range(1, 12)]

# plot the data
plt.plot(throughput)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side throughput (req/seq)")
plt.show()

plt.plot(mean_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side response time (milliseconds)")
plt.show()

