import os
import csv
import sys

dir = sys.argv[1]
case = sys.argv[2]

target = dir + "/summary.csv"

dir_list = os.listdir(dir)
dir_list.sort()

data = []


for d in dir_list:
    if d in ["summary.csv", "client_summary.csv", "plots"]:
        continue

    if case == "default":
        # default numbers case, there are no parameter values
        record = [d.split("_")[0], int(d.split("_")[1])]
    else:
        record = [d.split("_")[0], int(d.split("_")[1]), int(d.split("_")[4]), int(d.split("_")[5])]

    if case == "default":
        data_path = dir + "/" + d + "/default/" + "test_notes.csv"
    else:
        data_path = dir + "/" + d + "/" + "test_notes.csv"

    with open(data_path) as ff:
        reader = csv.reader(ff)

        for row in reader:
            if row[0] == "average throughput (req/sec)":
                record.append(row[1])
            elif row[0] == "average latency (ms)":
                record.append(row[1])

    data.append(record)

data.sort()

with open(target, "w") as f:
    writer = csv.writer(f)
    if case == "default":
        writer.writerow(["Mix", "Number of EBs", "Average Throughput (req/seq)", "Mean Latency (ms)"])
    else:
        writer.writerow(["Mix", "Number of EBs", "Apache MaxRequestWorkers",
                         "Tomcat Thread Pool Size", "Average Throughput (req/seq)", "Mean Latency (ms)"])

    for line in data:
        writer.writerow(line)
