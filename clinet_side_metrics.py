import requests
import matplotlib.pyplot as plt
import time
import csv
import os
import sys

throughput = []
mean_latency = []

folder_name = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"

# case_name = "shopping_200_tuning_without_apache"
case_name = sys.argv[2]
ru = int(sys.argv[3])
mi = int(sys.argv[4])
rd = int(sys.argv[5])
measuring_interval = int(sys.argv[6])

try:
    os.makedirs(folder_name+case_name)
except FileExistsError:
    print("directory already exists")
    # if input("are you sure want to go ahead (Y/n)?") == "n":
    #     exit()

out_filename = folder_name + case_name + "/client_data.csv"

# duration in seconds
duration = ru+mi+rd
# interval in seconds
interval = measuring_interval

# calculate the iterations from duration/interval
iterations = int(duration/interval)

# server is returning total request count
prev = requests.get("http://192.168.32.2:8080/performance?server=client").json()[1]

for _ in range(iterations):
    # server records results (mean latency, 99 latency etc.) for 40 seconds minute windows
    # (we can configure window interval in tomcat/webapps/tpc-w/WEB-INF/web.xml file)
    time.sleep(interval)
    res = requests.get("http://192.168.32.2:8080/performance?server=client").json()
    throughput.append(float(res[1] - prev)/interval)
    prev = res[1]
    mean_latency.append(res[2])

# save the configurations and average numbers in a file
with open(folder_name + case_name + "/client_summary.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["duration (seconds)", duration])
    writer.writerow(["measuring interval (seconds)", interval])
    writer.writerow(["average throughput (req/sec)", sum(throughput)/len(throughput)]) # TODO: This is not the correct number, should get the total count and divide by total time
    writer.writerow(["average latency (ms)", sum(mean_latency)/len(mean_latency)]) # TODO: this is avearge of 1 minute window latencies


# save the data
with open(out_filename, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["throughput", "latency"])

    for i in range(len(throughput)):
        writer.writerow([throughput[i], mean_latency[i]])

x_axis = [x*interval for x in range(iterations)]

# plot the data
plt.plot(x_axis, throughput)
plt.ylabel("server side throughput (req/seq) (20 seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/client_throughput.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, mean_latency)
plt.ylabel("server side latency (milliseconds) (40 seconds window)")
plt.xlabel("time (seconds)")
plt.savefig(folder_name + case_name + "/client_mean_latency.png", bbox_inches="tight")
plt.clf()

print("metrics collection complete")
