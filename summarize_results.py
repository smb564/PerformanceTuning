import os
import csv

dir = "apache_max_clients"
target = dir + "/summary.csv"

dir_list = os.listdir(dir)


with open(target, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Case", "Average Throughput (req/seq)", "Mean Latency (ms)"])
    for d in dir_list:

        record = [d, ]

        with open(dir + "/" + d + "/" + "test_notes.csv") as ff:
            reader = csv.reader(ff)

            for row in reader:
                if row[0] == "average throughput (req/sec)":
                    record.append(row[1])
                elif row[0] == "average latency (ms)":
                    record.append(row[1])

        writer.writerow(record)


