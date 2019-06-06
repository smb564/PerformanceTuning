# this script reads results and creates a table
import os
import csv


def get_percentage_increment(a, b, inverse=False):
    # a, b is assumed to be float
    # assume default, tuning order
    if a > b:
        return "-%.2f" % (a*100/b - 100) if not inverse else "+%.2f" % (a*100/b - 100)
    return "+%.2f" % (b*100/a - 100) if not inverse else "-%.2f" % (b*100/a - 100)


folder = "tuning_only_tomcat_gpopt"

data = []

for d in os.listdir(folder):
    if d == "summary.csv":
        continue

    record = [d.split("_")[0], int(d.split("_")[1])]  # case name, concurrency

    with open(folder + "/" + d + "/overall_results.csv") as f:
        f.readline()

        record.extend(map(float, f.readline().split(",")[1:3]))
        record.append(get_percentage_increment(record[-2], record[-1], inverse=False))

        record.extend(map(float, f.readline().split(",")[1:3]))
        record.append(get_percentage_increment(record[-2], record[-1], inverse=True))

    data.append(record)

data.sort()

with open(folder + "/summary.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Mix", "Concurrency", "Default Throughput (req/seq)", "Tuning Throughput (req/sec)",
                     "Percentage Increment", "Default RT (ms)", "Tuning RT (ms)", "Percentage Increment"])

    for line in data:
        writer.writerow(line)
