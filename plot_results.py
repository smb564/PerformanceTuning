import matplotlib.pyplot as plt
import csv

throughput = []
mean_latency = []

out_filename = "server_metrics/test_data.csv"

# duration in seconds
duration = 720
# interval in seconds
interval = 20

tuning_interval = 60  # in seconds (from bayesian_opt.py), -1 if not tuning


if tuning_interval != -1:
    tune_locations = [x*60.0/interval for x in range(1, 12)]

# plot the data
plt.plot(throughput)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side throughput (req/seq)")
plt.show()

plt.plot(mean_latency)
if tuning_interval != -1:
    for loc in tune_locations:
        plt.axvline(x=loc, color='r', linestyle='--')
plt.ylabel("server side response time (milliseconds)")
plt.show()