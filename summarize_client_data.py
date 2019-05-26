import os
import csv
import sys

def gospaces(temp, k):
    while temp[k] == " ":
        k += 1
    return k


def getend(temp, k):
    k = gospaces(temp, k)
    out = ""
    while temp[k] != "\n" and temp[k] != " ":
        out += temp[k]
        k += 1
    return out


def get(temp, term):
    k = temp.index(term) + len(term)
    return getend(temp, k)


def get_times(temp, term):
    k = temp.index(term) + len(term) + 5
    nums = []
    while temp[k:k + 2] != "];":
        num = ""
        while temp[k]!= "\n":
            num += temp[k]
            k += 1
        k += 1
        nums.append(int(num))
    return nums


def get_numbers(file_name):
    dataf = open(file_name)

    data = dataf.read()
    dataf.close()

    config = dict()

    # transaction mix
    config["mix"] = get(data, "Transaction Mix:")
    config["rampu_t"] = int(get(data, "Ramp-up time"))
    config["measure_t"] = int(get(data, "Measurement interval"))
    config["rampd_t"] = int(get(data, "Ramp-down time"))
    config["users"] = int(get(data, "EB Factory"))

    # print(config)

    endtimes = get_times(data, "endtimes")
    starttimes = get_times(data, "starttimes")
    wips = get_times(data, "wips")[:config["rampu_t"] + config["measure_t"] + config["rampd_t"]]

    average_throughput = sum(wips[config["rampu_t"]:config["rampu_t"] + config["measure_t"]+1])/float(config["measure_t"]+1)

    # print("Average throughput:", average_throughput)

    response_times = [endtimes[k] - starttimes[k] for k in range(len(endtimes))]

    rt_measure = []

    # get response times in measure interval
    for i in range(len(starttimes)):
        if config["rampu_t"]*1000 <= starttimes[i] <= (config["rampu_t"] + config["measure_t"])*1000:
            rt_measure.append(endtimes[i] - starttimes[i])

    # print len(rt_measure), "interactions inside the measurement interval"

    average_rt = sum(rt_measure)/float(len(rt_measure))
    # print("Average Response Time:", average_rt)
    return [average_throughput, average_rt]


if __name__ == "__main__":
    folder = sys.argv[1]
    records = [["Mix", "Number of EBs", "WIPS", "Response Time (ms)"]]

    for d in os.listdir(folder):
        if d != "summary.csv":
            record = [d.split("_")[0], int(d.split("_")[1])]
            record += get_numbers(folder + "/" + d + "/default.m")
            records.append(record)

    records.sort()

    with open(folder + "/summary.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(records)

