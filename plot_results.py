import matplotlib.pyplot as plt
import csv

save = True  # overwrite the previous plots

case = "browsing_400_tuning_without_apache"
dir = "server_metrics/" + case + "/"

with open(dir + "params.csv") as f:
    reader = csv.reader(f)
    duration = int(next(reader)[1])
    interval = int(next(reader)[1])
    tuning_interval = int(next(reader)[1])

throughput = []
mean_latency = []
threads = []

# read throughputs, latencies and threads
with open(dir + "data.csv") as f:
    reader = csv.reader(f)
    # skip the header of the csv
    next(reader)

    for row in reader:
        throughput.append(float(row[0]))
        mean_latency.append(float(row[1]))
        threads.append(float(row[2]))

if tuning_interval != -1:
    tune_locations = [x*tuning_interval for x in range(1, 12)]

x_axis = [x*interval for x in range(duration//interval)]

# plot the data
plt.plot(x_axis, throughput)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side throughput (req/seq) (20 seconds window)")

if save:
    plt.savefig(dir + "throughput.png", bbox_inches="tight")
    plt.clf()
else:
    plt.show()

plt.plot(x_axis, mean_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side latency (milliseconds) (60 seconds window)")

if save:
    plt.savefig(dir + "mean_latency.png", bbox_inches="tight")
    plt.clf()
else:
    plt.show()

plt.plot(x_axis, threads)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("Current Thread Count")

if save:
    plt.savefig(dir + 'thread_counts.png', bbox_inches='tight')
    plt.clf()
else:
    plt.show()

