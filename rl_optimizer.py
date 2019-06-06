import numpy as np
import requests
import time
import sys
import csv
import os

explored = set()


class RLOptimizer:

    def __init__(self, state2id, n_actions, step_size, model_path="", tuning_interval=-1, tune=False):
        self.state2id = state2id
        self.n_actions = n_actions
        self.step_size = step_size
        self.tuning_interval = tuning_interval

        # TODO : added 120 randomly. Usually the SLA is used.
        self.SLA_RT = 120  # SLA Response Time levels. To get the rewards using SLA - RT

        if tune:
            self.Q = model_path  # here the Q is passed as the model path
            self.data = []  # to keep track of the measurements
        else:
            self.Q = self._init_q(len(state2id), n_actions)
            self.model = np.load(model_path)  # this is the model (function) trained using the performance dataset

    def saveQ(self, path):
        np.save(path, self.Q)

    def loadQ(self, path):
        self.Q = np.load(path)

    def load_model(self, path):
        self.model = np.load(path)

    def pretrain(self, alpha, gamma, epsilon, iterations):
        # set the current param value to some known value
        # (apache, tomcat)
        s = (100, 100)

        for k in range(iterations):
            a = self._epsilon_greedy(epsilon, s)
            reward, s_ = self.perform_action(a, s)
            a_ = np.argmax(self.Q[state2id[s_], :])
            self.Q[state2id[s], a] += alpha * (reward + (gamma * self.Q[state2id[s_], a_]) - self.Q[state2id[s], a])
            s = s_
            epsilon *= 1.000004
            epsilon = min(epsilon, 0.9)

    def clean_q_table(self):
        self.Q = self._init_q(len(self.state2id), self.n_actions, self.step_size)

    def execute(self, alpha, gamma, epsilon, iterations):
        # s is the current configuration
        # let's always start with this
        s = (100, 100)
        requests.get("http://192.168.32.10:5001/setParam?MaxRequestWorkers=" + str(s[0]))
        requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(s[1]))
        requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(s[1]))

        param_history = []

        for k in range(iterations):
            a = self._epsilon_greedy(epsilon, s)
            reward, s_ = self.perform_action_real(a, s)
            a_ = np.argmax(self.Q[state2id[s_], :])
            self.Q[state2id[s], a] += alpha * (reward + (gamma * self.Q[state2id[s_], a_]) - self.Q[state2id[s], a])
            param_history.append(s)
            s = s_

        return param_history

    def _epsilon_greedy(self, epsilon, s, train=False):
        if train or np.random.rand() < epsilon:
            action = np.argmax(self.Q[state2id[s], :])
        else:
            action = np.random.randint(0, self.n_actions)

        # if the action if illogical (specifies params that are beyond the boundaries), get another action
        if s[0] == 20 and action == 1:
            return self._epsilon_greedy(epsilon, s, train)

        if s[1] == 20 and action == 4:
            return self._epsilon_greedy(epsilon, s, train)

        if s[0] == 400 and action == 0:
            return self._epsilon_greedy(epsilon, s, train)

        if s[1] == 400 and action == 3:
            return self._epsilon_greedy(epsilon, s, train)

        return action

    def _init_q(self, s, a):
        Q = np.zeros((s, a))

        # to remove illogical operations (which goes beyond the ranges)
        for i in range(20, 401, self.step_size):
            Q[state2id[(20, i)], 1] = -np.Infinity
            Q[state2id[(400, i)], 0] = -np.Infinity
            Q[state2id[(i, 20)], 4] = -np.Infinity
            Q[state2id[(i, 400)], 3] = -np.Infinity

        return Q

    def perform_action(self, a, s):
        if a == 0:
            s_ = (s[0] + self.step_size, s[1])
            reward = self._dummy_model(s_[0], s_[1])

        elif a == 1:
            s_ = (s[0] - self.step_size, s[1])
            reward = self._dummy_model(s_[0], s_[1])

        elif a == 3:
            s_ = (s[0], s[1] + self.step_size)
            reward = self._dummy_model(s_[0], s_[1])

        elif a == 4:
            s_ = (s[0], s[1] - self.step_size)
            reward = self._dummy_model(s_[0], s_[1])
        else:
            # no change
            s_ = s
            reward = self._dummy_model(s_[0], s_[1])
        return reward, s_

    @staticmethod
    def _function(x, a, b, c, d, e, f):
        return a * x[0] ** 2 + b * x[1] ** 2 + c * x[0] * x[1] + d * x[0] + e * x[1] + f

    def _func(self, x, pcor):
        return self._function(x, pcor[0], pcor[1], pcor[2], pcor[3], pcor[4], pcor[5])

    def _dummy_model(self, x1, x2):
        explored.add((x1, x2))
        pcor = self.model
        return self.SLA_RT - self._func([x1, x2], pcor)

    def _get_reward(self, interval):
        """ This method measure the performance for the given period """
        time.sleep(interval)

        # measure performance
        res = requests.get("http://192.168.32.2:8080/performance?server=apache").json()
        self.data.append(res)
        return self.SLA_RT - res[2]

    def perform_action_real(self, a, s):
        if a == 0:
            # increase Apache
            s_ = (s[0] + step_size, s[1])
            requests.get("http://192.168.32.10:5001/setParam?MaxRequestWorkers=" + str(s_[0]))

        elif a == 1:
            # decrease Apache
            s_ = (s[0] - step_size, s[1])
            requests.get("http://192.168.32.10:5001/setParam?MaxRequestWorkers=" + str(s_[0]))

        elif a == 3:
            # increase Tomcat
            s_ = (s[0], s[1] + step_size)
            requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(s_[1]))
            requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(s_[1]))

        elif a == 4:
            # decrease Tomcat
            s_ = (s[0], s[1] - step_size)
            requests.put("http://192.168.32.2:8080/setparam?name=minSpareThreads&value=" + str(s_[1]))
            requests.put("http://192.168.32.2:8080/setparam?name=maxThreads&value=" + str(s_[1]))
        else:
            # no change
            s_ = s
        reward = self._get_reward(self.tuning_interval)
        return reward, s_


def pre_train_and_save(alpha, gamma, state2id, model_path, q_path):
    epsilon = 0.1
    iterations = 1000000
    opt = RLOptimizer(state2id, n_actions, step_size, model_path)
    opt.pretrain(alpha, gamma, epsilon, iterations)
    print(len(explored), len(state2id))

    print("Saving Q table..")
    np.save(q_path, opt.Q)


def tune(alpha, gamma, epsilon, state2id, q_path, iterations, tuning_interval):
    Q = np.load(q_path)
    opt = RLOptimizer(state2id, n_actions, step_size, Q, tuning_interval, tune=True)
    param_history = opt.execute(alpha, gamma, epsilon, iterations)
    data = opt.data
    return param_history, data


# sys args
# if pretrain: 1-"pretrain" 2-model folder 3-case name 4-q folder
# if using: 1-"tune" 2-q folder 3 - folder name 4 - case name 5-ru 6-mi 7-rd 8-tuning interval
if __name__ == "__main__":
    alpha = 0.4
    gamma = 0.75

    step_size = 20
    state2id = {}
    n_actions = 6  # increase, decrease, no change --> Apache, same for tomcat

    for i in range(20, 401, step_size):
        for j in range(20, 401, step_size):
            state2id[(i, j)] = len(state2id)

    if sys.argv[1].lower() == "pretrain":
        model_folder = sys.argv[2] if sys.argv[2][-1] == "/" else sys.argv[2] + "/"
        case = sys.argv[3]
        q_folder = sys.argv[4] if sys.argv[4][-1] == "/" else sys.argv[4] + "/"

        pre_train_and_save(alpha, gamma, state2id, model_folder + case + ".npy", q_folder + case + "_Q.npy")

    elif sys.argv[1].lower() == "tune":
        # use the pre-trained model to tune
        q_folder = sys.argv[2] if sys.argv[2][-1] == "/" else sys.argv[2] + "/"
        folder_name = sys.argv[3]
        case_name = sys.argv[4]
        ru = int(sys.argv[5])
        mi = int(sys.argv[6])
        rd = int(sys.argv[7])
        tuning_interval = int(sys.argv[8])

        test_duration = ru + mi + rd
        iterations = test_duration // tuning_interval
        param_history, data = tune(alpha, gamma, 0.9, state2id, q_folder + case_name + "_Q.npy", iterations, tuning_interval)

        try:
            os.makedirs(folder_name + "/" + case_name)
        except FileExistsError:
            print("directory already exists")

        with open(folder_name + "/" + case_name + "/results.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["IRR", "Request Count", "Mean Latency (for window)", "99th Latency"])
            for line in data:
                writer.writerow(line)

        with open(folder_name + "/" + case_name + "/param_history.csv", "w") as f:
            writer = csv.writer(f)
            for line in param_history:
                writer.writerow(line)

        print("Optimization complete")

    else:
        print("ERROR: arg 1 should either be 'pretrain' or 'tune'")

