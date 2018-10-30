#!/usr/bin/env python


import sys
import os
import optparse
import random
import numpy as np

# Set "SUMO_HOME" as environment variable
# os.environ["SUMO_HOME"] = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# print(os.environ["SUMO_HOME"])

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci  # noqa
from sumolib import checkBinary  # noqa

# Import signal timing logic classes
from Logic import Logic
from LogicFixed import LogicFixed as Fixed
from LogicActuated import LogicActuated as Actuated
from LogicRL import LogicRL as RL
# from deep_neural import Network
from DeepLearningPython35.network import Network

# Left turn phase policy from {protected, protected-permissive, split-protect-NS, split-protect-EW, unrestricted}
left_policy = "protected-permissive"
# Left turn phase policy from {Fixed, Actuated, RL}. All must implement: get_phase(self, current_phases)
logic = Actuated(left_policy)
if not issubclass(type(logic), Logic):
    raise ValueError('logic must be a sub class of Logic')

# The time interval (seconds) for each line of data in the demand file. 5 minutes in UTDOT logs (https://udottraffic.utah.gov/ATSPM)
data_interval = 300
right_on_red = True  # Do we allow vehicles to turn right on red
min_phase_time = 3  # the minimal time interval between signal change (including yellow phase)


# time in seconds and demand as a list of entries from the demand file "State_Street_4500_South.txt"
def vehicle_generator(time, demand):

    # Indexes for demand file
    iEL = 2  # Index for Eastbound turning left...
    iET = 3
    iETR = 4

    iWL = 6
    iWT = 7
    iWTR = 8

    iNL = 10
    iNT = 11
    iNR = 12

    iSL = 14
    iST = 15
    iSR = 16

    indexes = [iEL, iET, iETR, iWL, iWT, iWTR, iNL, iNT, iNR, iSL, iST, iSR]
    routes = ["Eastbound.L", "Eastbound.T", "Eastbound.TR", "Westbound.L", "Westbound.T", "Westbound.TR",
              "Northbound.L", "Northbound.T", "Northbound.R", "Southbound.L", "Southbound.T", "Southbound.R"]

    # The data entry for the current time interval is retrieved
    data = demand[int(time/data_interval)].split()
    probabilities = []

    vehicles = []
    for x in range(len(indexes)):
        # The probability of generating a vehicle per time step for each route
        p = float(data[indexes[x]]) / data_interval
        # in the current time interval
        if random.uniform(0, 1) < p:
            vehicle = [routes[x], "passenger"]
            vehicles.append(vehicle)
    return vehicles


def set_phase(indexes):

    phases = []

    # Specify the green lanes in each phase
    # phases.insert(6,[5,6,7,8])  # phase Through, Right. Westbound
    # phases.insert(2,[16,17,18,19])  # phase Through, Right. Eastbound
    # phases.insert(8,[11,12,13,14])  # phase Through, Right. Northbound
    # phases.insert(4,[0,1,2,3])  # phase Through, Right. Southbound
    #
    # phases.insert(1,[9,10])  # phase Left. Westbound
    # phases.insert(5,[20,21])  # phase Left. Eastbound
    # phases.insert(3,[15])  # phase Left. Northbound
    # phases.insert(7,[4])  # phase Left. Southbound
    phases.insert(0, [])
    phases.insert(1, [9, 10])  # phase Left. Westbound
    phases.insert(2, [16, 17, 18, 19])  # phase Through, Right. Eastbound
    phases.insert(3, [15])  # phase Left. Northbound
    phases.insert(4, [0, 1, 2, 3])  # phase Through, Right. Southbound
    phases.insert(5, [20, 21])  # phase Left. Eastbound
    phases.insert(6, [5, 6, 7, 8])  # phase Through, Right. Westbound
    phases.insert(7, [4])  # phase Left. Southbound
    phases.insert(8, [11, 12, 13, 14])  # phase Through, Right. Northbound

    right_turns = [0, 5, 11, 16]
    next_signals = list("rrrrrrrrrrrrrrrrrrrrrr")  # init signals

    if right_on_red:
        for x in right_turns:
            # init right turns to green light "lower case 'g' mean that the stream has to decelerate"
            next_signals[x] = 'g'

    for i in indexes:
        for x in phases[i]:
            next_signals[x] = 'G'

    current_signals = list(traci.trafficlights.getRedYellowGreenState(
        "gneJ1"))  # get the currently assigned lights
    yellow_phase = False
    for x in range(len(current_signals)):
        if current_signals[x] == 'G' and next_signals[x] == 'r':  # Check if a yellow phase is needed
            yellow_phase = True

    if yellow_phase:
        for x in range(len(current_signals)):
            # If a yellow phase is needed then find which lanes
            if current_signals[x] == 'G' and next_signals[x] == 'r':
                                                                   # should be assigned yellow
                current_signals[x] = 'y'
        traci.trafficlights.setRedYellowGreenState("gneJ1", ''.join(current_signals))
        return False
    else:
        traci.trafficlights.setRedYellowGreenState("gneJ1", ''.join(next_signals))
        return True

# __________________________________ this is for training DQN


def get_state(current_phase):
    # the state of Q function:
    # s = (a, jamlength for all lanes): a is integer of {0,1,2,3} for 4 rings
    getID = {0: 'S0', 1: 'S1', 2: 'S2', 3: 'S3', 4: 'S4', 5: 'W0', 7: 'W1', 8: 'W2', 9: 'W3', 10: 'W4',
             11: 'N0', 12: 'N1', 13: 'N2', 14: 'N3', 15: 'N4', 16: 'E0', 18: 'E1', 19: 'E2', 20: 'E3', 21: 'E4'}
    lane_jam, lane_jam_count = [], []
    for i in getID:
        lane = 'laneAreaDetector.'+getID[i]
        lane_jam_count.append(traci.areal.getLastStepMeanSpeed(lane))
        # lane_jam.append(traci.areal.getLastStepMeanSpeed(lane))
    table_prot_perm = [[1, 5], [1, 5, 2, 6], [3, 7], [3, 7, 4, 8]]
    try:
        light_info = [table_prot_perm.index(current_phase)]
    except:
        light_info = [0]
    # return light_info+lane_jam
    return lane_jam_count + light_info
    # # tranform to a matrix
    # state = np.zeros((22, 1))
    #
    # for i in range(22):
    #     state[i] = total_state[i]
    # return state


def act_lights(action, current_phase):
    # action from the NN is 0 & 1, where 1 is move to next ring, 0 is stay current light
    if action == 0:
        return -1
    elif action == 1:
        table_prot_perm = [[1, 5], [1, 5, 2, 6], [3, 7], [3, 7, 4, 8]]
        try:
            next_index = (table_prot_perm.index(current_phase) + 1) % 4
        except:
            next_index = 0
        return table_prot_perm[next_index]


def get_reward(cur_state, next_state):
    # The reward will be the difference of all jamped Vehicles
    # cur_jam = sum(cur_state[:-1])
    # next_jam = sum(next_state[:-1])
    # return cur_jam - next_jam
    return -sum(cur_state) + sum(next_state)


def transform(cur_state, action, Q):
    x = cur_state + [action]
    x_, y_ = np.ones((23, 1)), np.zeros((1, 1))
    for i in range(22):
        x_[i] = x[i]

    y_[0] = Q
    return (x_, y_)


def transform_x(cur_state, action):
    x = cur_state + action
    x_ = np.zeros((22, 1))
    print(x)
    for i in range(22):
        x_[i] = x[i]
    return x_


def run():
    # initialize Q, theta, ect
    import time

    actions = [1, 0]  # ['change', 'stay']
    Memory = []  # will be tuple of (x,y) ,x is state, y is Q value

    dql = Network([23, 50, 1])  # a 3-layer network, with last layer is output
    Q = 0  # Q value
    epochs = 200
    simu_steps = 0
    N = 3000
    num_epoch = 0
    end_point = 45000

    for M in range(epochs):

        traci.start([sumoBinary, "-c", "Data/State_Street_4500_South.sumocfg", "--tripinfo-output",
                     "tripinfo.xml"])  # ,  "--time-to-teleport -1"
        with open('State_Street_4500_South.txt', 'r') as fp:  # Load the demand file
            demand = fp.readlines()

        demand.pop(0)
        demand.pop(0)  # The two first entries are the file header, depose them

        vehNr = 0  # Vehicles dynamic count
        # N = 57600  # number of time steps (seconds) total 16 hours
        # N = 30*300  # number of time steps (seconds) total 16 hours

        last_phase_change = 0  # The last time the signals have changed
        current_phase = [2, 6]  # currently green phases index
        yellow = False  # indicates whether the current phase is yellow
        num_epoch += 1
        print('start training %dth eposide' % num_epoch, 'total steps,', simu_steps)
        start_time = time.time()
        # simu_steps = 0
        cur_state = get_state(current_phase)
        action = 0
        # Q should goes to 0 every time restart
        Q = 0
        # The +300 is to allow all vehicles (generated up to time N) to clear the network
        while int(traci.simulation.getCurrentTime()*0.001) < N:
            # cur_state = get_state(current_phase)
            # print('cur_state:', cur_state)

            vehicles = vehicle_generator(int(traci.simulation.getCurrentTime()*0.001), demand)
            for v in vehicles:
                traci.vehicle.add(str(vehNr), v[0], typeID=v[1])
                vehNr += 1
            # print(int(traci.simulation.getCurrentTime()*0.001), last_phase_change)
            if int(traci.simulation.getCurrentTime()*0.001) - last_phase_change >= min_phase_time:

                # Q learning

                next_state = get_state(current_phase)
                # reward = get_reward(cur_state, next_state)
                reward = get_reward(cur_state, next_state)
                NextQ = []
                simu_steps += 1
                # print(simu_steps)
                if simu_steps % 1000 == 0:
                    print('shoud save here for %dth training', simu_steps)
                    dql.save(simu_steps)

                if simu_steps == end_point:
                    break
                # Q learning !!!!!!!!!!!!!!!!
                if simu_steps < int(traci.simulation.getCurrentTime()*0.001) - 1:  # TODO:
                    for i in range(2):
                        NextQ.append(np.max(dql.feedforward(next_state + [i, 1])))
                    Q = reward + gamma * max(NextQ)
                else:
                    Q = reward

                # replay!!!!!!!!
                Memory.append(transform(cur_state, action, Q))  # mini_batch data for (x,y)
                dql.SGD(Memory, epochs=30, mini_batch_size=10, eta=0.5, test_data=None)
                # update cur_state
                cur_state = next_state
                # cur_jam = next_jam

                if yellow:
                    next_phase = current_phase
                    # if yellow, no action took place
                    action = 0
                else:

                    # # action = dql.get_action(cur_state)
                    # # next_phase = act_lights(action, current_phase)  # dql.act(current_phase)
                    # next_state = get_state(current_phase)
                    # reward = get_reward(cur_state, next_state)
                    # NextQ = []
                    # simu_steps += 1
                    # print(simu_steps)
                    # # Q learning !!!!!!!!!!!!!!!!
                    # if simu_steps < somtthing:  # TODO:
                    #     for i in range(2):
                    #         NextQ.append(np.argmax(dql.feedforward(next_state+[i])))
                    #     Q += reward + gamma * max(NextQ)
                    # else:
                    #     Q += reward
                    #
                    # # replay!!!!!!!!
                    # Memory.append(transform(cur_state, action, Q))  # mini_batch data for (x,y)
                    # dql.SGD(Memory, epochs=1, mini_batch_size=100, eta=0.1, test_data=None)
                    # # update cur_state
                    # cur_state = next_state
                    # # make decision based on replay model
                    action = dql.get_action(cur_state)
                    next_phase = act_lights(action, current_phase)  # dql.act(current_phase

                if next_phase != -1:  # If a phase change is required
                    current_phase = next_phase  # chosen phases index
                    if set_phase(next_phase):  # If the chosen phases are applicable (no yellow transition is required)
                        yellow = False
                    else:
                        yellow = True
                    last_phase_change = int(traci.simulation.getCurrentTime()*0.001)

                # wait for next state

            traci.simulationStep()
            # print('shoud save here for %dth episode', M)
            # dql.save(M)
            # next_state = get_state(next_phase)
            # reward = get_reward(cur_state, next_state)
            # NextQ = []
            #
            # if simu_steps < somtthing:  # TODO:
            #     for i in range(2):
            #         NextQ.append(np.argmax(dql.feedforward(next_state+[i])))
            #     Q += reward + gamma * max(NextQ)
            # else:
            #     Q += reward
            # # transform the data into matrix form
            # Memory.append(transform(cur_state, action, Q))  # mini_batch data for (x,y)
            #
            # state = next_state
            # simu_steps += 1
            # dql.SGD(Memory, epochs=1 mini_batch_size=500, eta=0.1, test_data=None)
            # print(simu_steps)

        # traci.close()
        # print(Memory)
        # dql.SGD(Memory, epochs=30, mini_batch_size=10, eta=0.1, test_data=None)
        print('shoud save here for %dth episode', M)
        dql.save(M)
        sys.stdout.flush()
        # print('----------------(%d)th eposide ends, training time (%f)' %
        #       (num_epoch, time.time() - start_time))
        # if num_epoch % 2 == 0:
        #     print('shoud save here for (%d)th training', num_epoch)
        #     dql.save(num_epoch)
    traci.close()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    gamma = 0.3
    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    sumoBinary = checkBinary('sumo')
    # if options.nogui:
    #     sumoBinary = checkBinary('sumo')
    # else:
    #     sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    # traci.start([sumoBinary, "-c", "Data/State_Street_4500_South.sumocfg", "--tripinfo-output",
    #              "tripinfo.xml"])  # ,  "--time-to-teleport -1"
    run()
