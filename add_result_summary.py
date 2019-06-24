import sys
import requests
import csv

if sys.argv[0] == "start":
    # create the file with the headers
    folder = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"
    with open(folder + "summary.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Number of EBs", "Arrival Rate (Throughput)", "Average Response Time (ms)",
                         "99p Latency (ms)", "Std Dev", "Errors"])

else:
    ru = int(sys.argv[0])
    mi = int(sys.argv[1])
    rd = int(sys.argv[2])

    folder = sys.argv[3] if sys.argv[3][-1] == "/" else sys.argv[3] + "/"

    num_ebs = int(sys.argv[4])

    res = requests.get("http://192.168.32.2:8080/performance-mi").json()

    if len(res) == 2:
        print("error occurred when retrieving values for the measuring interval!")
        with open(folder + "summary.csv", "a+") as f:
            writer = csv.writer(f)
            writer.writerow([-1, -1])
    else:
        with open(folder + "summary.csv", "a+") as f:
            writer = csv.writer(f)
            writer.writerow([num_ebs, res[1] / mi, res[2], res[3], res[4], res[5]])
