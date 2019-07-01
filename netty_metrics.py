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
std_devs = []
errors = []

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"

# case_name = "shopping_200_tuning_without_apache"
case_name = sys.argv[2]
ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
measuring_interval = int(sys.argv[6])
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

tuning_interval = -1

# server is returning total request count
prev = requests.get("http://192.168.32.2:8080/performance-netty").json()[1]

current_time = time.time()

for _ in range(iterations):
    # server records results (mean latency, 99 latency etc.) for 1 minute windows
    print(current_time + interval - time.time(), interval)
    time.sleep(current_time + interval - time.time())
    current_time += interval
    res = requests.get("http://192.168.32.2:8080/performance-netty").json()
    print(res)
    throughput.append(float(res[1] - prev)/interval)
    prev = res[1]
    mean_latency.append(res[2])
    p99_latency.append(res[3])
    std_devs.append(res[4])
    errors.append(res[5])
    threads.append(requests.get("http://192.168.32.2:8080/getThreadPoolNetty").json())


# save the configurations and average numbers in a file
with open(folder_name + case_name + "/test_notes.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["duration (seconds)", duration])
    writer.writerow(["measuring interval (seconds)", interval])
    writer.writerow(["tuning interval (seconds)", tuning_interval])
    writer.writerow(["average throughput (req/sec)", sum(throughput)/len(throughput)]) # TODO: This is not the correct number, should get the total count and divide by total time
    writer.writerow(["average latency (ms)", sum(mean_latency)/len(mean_latency)]) # TODO: this is avearge of 1 minute window latencies
    # let's take the average for the measuring interval from the server
    # res = requests.get("http://192.168.32.2:8080/performance-mi").json()
    # writer.writerow(["average throughput (req/sec)", res[1] / mi])
    writer.writerow(["average latency (ms)", res[2]])
    writer.writerow(["99p latency (ms)", res[3]])


# save the data
with open(out_filename, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["throughput", "latency", "threads", "p99 latency", "std dev", "errors"])

    for i in range(len(throughput)):
        writer.writerow([throughput[i], mean_latency[i], threads[i], p99_latency[i], std_devs[i], errors[i]])

x_axis = [x*interval for x in range(iterations)]

# plot the data
plt.plot(x_axis, throughput)
plt.ylabel("Server Side Throughput (req/seq) (" + str(measuring_interval) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/throughput.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, mean_latency)
plt.ylabel("Server Side Latency (milliseconds) (" + str(measuring_window) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/mean_latency.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, threads)
plt.ylabel("Current Thread Count")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + '/thread_counts.png', bbox_inches='tight')
plt.clf()

plt.plot(x_axis, p99_latency)
plt.ylabel("Server Side 99th Percentile Latency (milliseconds) (" + str(measuring_window) + " seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/p99_latency.png", bbox_inches="tight")
plt.clf()

print("metrics collection complete")
