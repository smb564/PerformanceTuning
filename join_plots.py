import matplotlib.pyplot as plt
import csv
import os


def get_data(case):
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

    return [throughput, mean_latency, threads, duration, interval, tuning_interval]


case_name = "browsing_200_default_tuning"  # to make the folder name
case1 = "browsing_200_default_without_apache"
case2 = "browsing_200_tuning_without_apache"

data1 = get_data(case1)
data2 = get_data(case2)

# assuming tuning interval, interval, and duration are same (to joing plots they should be equal)
duration = data2[3]
interval = data2[4]

dir = "joint_plots/" + case_name

# create a directory
try:
    os.makedirs(dir)
except FileExistsError:
    print("directory already exists")
    if input("are you sure want to go ahead (Y/n)?") == "n":
        exit()

dir += "/"

# if tuning_interval != -1:
#     tune_locations = [x*tuning_interval for x in range(1, 12)]

x_axis = [x*interval for x in range(duration//interval)]

plt.plot(x_axis, data1[0], color='b', label='default')
plt.plot(x_axis, data2[0], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("throughput (req/sec) (20 second window)")
plt.legend()
plt.savefig(dir + "throughput.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, data1[1], color='b', label='default')
plt.plot(x_axis, data2[1], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("server side latency (milliseconds) (60 seconds window)")
plt.legend()
plt.savefig(dir + "latency.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, data1[2], color='b', label='default')
plt.plot(x_axis, data2[2], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("Current Thread Count")
plt.legend()
plt.savefig(dir + "thread_counts.png", bbox_inches="tight")
plt.clf()
