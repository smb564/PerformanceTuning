import matplotlib.pyplot as plt
import csv
import sys


def get_data(folder_name, case):
    directory = folder_name + "/" + case + "/"

    with open(directory + "test_notes.csv") as f:
        reader = csv.reader(f)
        duration = int(next(reader)[1])
        interval = int(next(reader)[1])
        tuning_interval = int(next(reader)[1])
        average_throughput = float(next(reader)[1])
        average_latency = float(next(reader)[1])

    throughput = []
    mean_latency = []
    threads = []

    # read throughputs, latencies and threads run
    with open(directory + "data.csv") as f:
        reader = csv.reader(f)
        # skip the header of the csv
        next(reader)

        for row in reader:
            throughput.append(float(row[0]))
            mean_latency.append(float(row[1]))
            threads.append(float(row[2]))

    return [throughput, mean_latency, threads, duration, interval, tuning_interval, average_throughput, average_latency]


folder = sys.argv[1] if sys.argv[1][-1] != "/" else sys.argv[:-1]
case1 = sys.argv[2]  # default data
case2 = sys.argv[3]  # tuning data

data1 = get_data(folder, case1)
data2 = get_data(folder, case2)

# assuming tuning interval, interval, and duration are same (to joing plots they should be equal)
duration = data2[3]
interval = data2[4]

target_dir = folder + "/"

# if tuning_interval != -1:
#     tune_locations = [x*tuning_interval for x in range(1, 12)]

x_axis = [x*interval for x in range(duration//interval)]

plt.plot(x_axis, data1[0], color='b', label='default')
plt.plot(x_axis, data2[0], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("throughput (req/sec) (20 second window)")
plt.legend()
plt.savefig(target_dir + "throughput.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, data1[1], color='b', label='default')
plt.plot(x_axis, data2[1], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("server side latency (milliseconds) (60 seconds window)")
plt.legend()
plt.savefig(target_dir + "latency.png", bbox_inches="tight")
plt.clf()

plt.plot(x_axis, data1[2], color='b', label='default')
plt.plot(x_axis, data2[2], color='r', label='tuning')
plt.xlabel("time (seconds)")
plt.ylabel("Current Thread Count")
plt.legend()
plt.savefig(target_dir + "thread_counts.png", bbox_inches="tight")
plt.clf()

with open(target_dir + "overall_results.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["", "default", "tuning"])
    writer.writerow(["average throughput (req/sec)", data1[6], data2[6]])
    writer.writerow(["average latency (ms)", data1[7], data2[7]])
