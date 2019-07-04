import sys
import csv


def get_queue_length_stats(content):
    result = [['runq-sz',  'plist-sz',   'ldavg-1',   'ldavg-5',  'ldavg-15',   'blocked']]
    content = content.split("\n")
    content = content[3:]

    summary = [['runq-sz',  'plist-sz',   'ldavg-1',   'ldavg-5',  'ldavg-15',   'blocked']]

    for line in content:
        if line.startswith("Average"):
            line = line.strip().split(" ")
            new_line= []
            for i in line:
                if len(i.strip()) != 0:
                    new_line.append(i)
            summary.append(new_line[1:])
        else:
            line = line.strip().split(" ")
            new_line= []
            for i in line:
                if len(i.strip()) != 0:
                    new_line.append(i)
            result.append(new_line[2:])

    return summary, result


summary, result = get_queue_length_stats(sys.stdin.read())

save_path = sys.argv[1] if sys.argv[1][-1] == "/" else sys.argv[1] + "/"

with open(save_path + "load_average_summary.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(summary)

with open(save_path + "load_average_all.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(result)
