import requests
import matplotlib.pyplot as plt
import time
import csv
import os
import sys

throughput = []
mean_latency = []
threads = []
p99_latency = []

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"

# case_name = "shopping_200_tuning_without_apache"
case_name = sys.argv[2]
ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
measuring_interval = int(sys.argv[6])
measuring_window = 60

if len(sys.argv) == 8:
    # measuring window is provided
    measuring_window = int(sys.argv[7])

try:
    os.makedirs(folder_name+case_name)
except FileExistsError:
    print("directory already exists")
    # if input("are you sure want to go ahead (Y/n)?") == "n":
    #     exit()

out_filename = folder_name + case_name + "/data.csv"

# duration in seconds
duration = ru+mi+rd
# interval in seconds
interval = measuring_interval

# calculate the iterations from duration/interval
iterations = int(duration/interval)

tuning_interval = -1  # in seconds (from bayesian_opt.py), -1 if not tuning TODO: Set the correct value every time

# server is returning total request count

prev = requests.get("http://192.168.32.2:8080/performance?server=apache").json()[1]

for _ in range(iterations):
    # server records results (mean latency, 99 latency etc.) for 1 minute windows
    # (we can configure window interval in tomcat/webapps/tpc-w/WEB-INF/web.xml file)
    time.sleep(interval)
    res = requests.get("http://192.168.32.2:8080/performance?server=apache").json()
    throughput.append(float(res[1] - prev)/interval)
    prev = res[1]
    mean_latency.append(res[2])
    p99_latency.append(res[3])

    # get the current thread pool size as well
    threads.append(requests.get("http://192.168.32.2:8080/getparam?name=poolSize").json())

# save the configurations and average numbers in a file
with open(folder_name + case_name + "/test_notes.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["duration (seconds)", duration])
    writer.writerow(["measuring interval (seconds)", interval])
    writer.writerow(["tuning interval (seconds)", tuning_interval])
    writer.writerow(["average throughput (req/sec)", sum(throughput)/len(throughput)]) # TODO: This is not the correct number, should get the total count and divide by total time
    writer.writerow(["average latency (ms)", sum(mean_latency)/len(mean_latency)]) # TODO: this is avearge of 1 minute window latencies


# save the data
with open(out_filename, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["throughput", "latency", "threads", "p99 latency"])

    for i in range(len(throughput)):
        writer.writerow([throughput[i], mean_latency[i], threads[i], p99_latency[i]])

if tuning_interval != -1:
    tune_locations = [x*tuning_interval for x in range(1, 12)]

x_axis = [x*interval for x in range(iterations)]

# plot the data
plt.plot(x_axis, throughput)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side throughput (req/seq) (" + str(measuring_interval) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/throughput.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, mean_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side latency (milliseconds) (" + str(measuring_window) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/mean_latency.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, threads)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("Current Thread Count")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + '/thread_counts.png', bbox_inches='tight')
plt.clf()

plt.plot(x_axis, p99_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side 99th percentile latency (milliseconds) (" + str(measuring_window) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/p99_latency.png", bbox_inches="tight")
plt.clf()

print("metrics collection complete")
