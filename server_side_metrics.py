import requests
import matplotlib.pyplot as plt
import time
import csv
import os

throughput = []
mean_latency = []
threads = []

case_name = "browsing_default"
try:
    os.makedirs("server_metrics/"+case_name)
except FileExistsError:
    print("directory already exists")

out_filename = "server_metrics/" + case_name + "/data.csv"

# duration in seconds
duration = 720
# interval in seconds
interval = 20

# calculate the iterations from duration/interval
iterations = int(duration/interval)

tuning_interval = -1  # in seconds (from bayesian_opt.py), -1 if not tuning

# save the configurations in a file
with open("server_metrics/" + case_name + "/params.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["duration (seconds)", duration])
    writer.writerow(["measuring interval (seconds)", interval])
    writer.writerow(["tuning interval (seconds)", tuning_interval])

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

    # get the current thread pool size as well
    threads.append(requests.get("http://192.168.32.1:8080/getparam?name=minSpareThreads").json())

# save the data
with open(out_filename, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["throughput", "latency", "threads"])

    for i in range(len(throughput)):
        writer.writerow([throughput[i], mean_latency[i], threads[i]])

if tuning_interval != -1:
    tune_locations = [x*60.0/interval for x in range(1, 12)]

# plot the data
plt.plot(throughput)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side throughput (req/seq)")
plt.savefig("server_metrics/" + case_name + "/throughput.png", bbox_inches="tight")

plt.plot(mean_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side response time (milliseconds)")
plt.savefig("server_metrics/" + case_name + "/mean_latency.png", bbox_inches="tight")

plt.plot(threads)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("Current Thread Count")
plt.savefig("server_metrics/" + case_name + '/thread_counts.png', bbox_inches='tight')