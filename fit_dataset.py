from scipy.optimize import curve_fit
import pandas
import numpy as np


def function(x, a, b, c, d, e, f):
    # print("x0", x[0])
    # print("x1", x[1])
    return a*x[0]**2 + b*x[1]**2 + c*x[0]*x[1] + d*x[0] + e*x[1] + f


def func(x, pcor):
    return function(x, pcor[0], pcor[1], pcor[2], pcor[3], pcor[4], pcor[5])


for mix in ["browsing", "shopping", "ordering"]:
    for ebs in [50, 100, 150, 200]:
        # TODO: not the most efficient, can read once and filter and save. Do it later.
        # read data file
        data = pandas.read_csv("tpcw_results_dataset/summary.csv")
        # print(data.loc[data["Number of EBs"] == 100].loc[data["Mix"] == "browsing"])
        data = data.loc[data["Number of EBs"] == ebs].loc[data["Mix"] == mix,
                                                          ["Apache MaxRequestWorkers", "Tomcat Thread Pool Size",
                                                           "Average Throughput (req/seq)", "Mean Latency (ms)"]]

        xdata = []
        ydata = []

        for index, row in data.iterrows():
            xdata.append([row["Apache MaxRequestWorkers"], row["Tomcat Thread Pool Size"]])
            ydata.append(row["Mean Latency (ms)"])

        xdata = np.array(xdata).T
        ydata = np.array(ydata)

        popt, pcor = curve_fit(function, xdata, ydata)

        np.save("polynomials/" + mix + "_" + str(ebs) + ".npy", popt)
