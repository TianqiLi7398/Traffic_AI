#!/usr/bin/env python


import sys
import os
import optparse
import random

# Set "SUMO_HOME" as environment variable
#os.environ["SUMO_HOME"] = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# print(os.environ["SUMO_HOME"])

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(
        os.environ['SUMO_HOME'], 'tools')
    sys.path.append(
        tools)
else:
    sys.exit(
        "please declare environment variable 'SUMO_HOME'")
import traci  # noqa
from sumolib import checkBinary  # noqa

# Import signal timing logic classes
from Logic import Logic
from LogicFixed import LogicFixed as Fixed
from LogicActuated import LogicActuated as Actuated
from LogicRL import LogicRL as RL

# Left turn phase policy from {protected, protected-permissive, split-protect-NS, split-protect-EW, unrestricted}
left_policy = "protected-permissive"
# Left turn phase policy from {Fixed, Actuated, RL}. All must implement: get_phase(self, current_phases)
logic = RL(
    left_policy)

if not issubclass(type(logic), Logic):
    raise ValueError(
        'logic must be a sub class of Logic')

# The time interval (seconds) for each line of data in the demand file. 5 minutes in UTDOT logs (https://udottraffic.utah.gov/ATSPM)
data_interval = 300
# Do we allow vehicles to turn right on red
right_on_red = True
# the minimal time interval between signal change (including yellow phase)
min_phase_time = 3


# time in seconds and demand as a list of entries from the demand file "State_Street_4500_South.txt"
def vehicle_generator(time, demand):

    # Indexes for demand file
    # Index for Eastbound turning left...
    iEL = 2
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

    indexes = [iEL, iET, iETR, iWL, iWT,
               iWTR, iNL, iNT, iNR, iSL, iST, iSR]
    routes = ["Eastbound.L", "Eastbound.T", "Eastbound.TR", "Westbound.L", "Westbound.T", "Westbound.TR",
              "Northbound.L", "Northbound.T", "Northbound.R", "Southbound.L", "Southbound.T", "Southbound.R"]

    # The data entry for the current time interval is retrieved
    data = demand[int(
        time/data_interval)].split()
    probabilities = []

    vehicles = []
    for x in range(len(indexes)):
        # The probability of generating a vehicle per time step for each route
        p = float(
            data[indexes[x]]) / data_interval
        # in the current time interval
        if random.uniform(0, 1) < p:
            vehicle = [
                routes[x], "passenger"]
            vehicles.append(
                vehicle)
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
    phases.insert(
        0, [])
    # phase Left. Westbound
    phases.insert(
        1, [9, 10])
    # phase Through, Right. Eastbound
    phases.insert(
        2, [16, 17, 18, 19])
    # phase Left. Northbound
    phases.insert(
        3, [15])
    # phase Through, Right. Southbound
    phases.insert(
        4, [0, 1, 2, 3])
    # phase Left. Eastbound
    phases.insert(
        5, [20, 21])
    # phase Through, Right. Westbound
    phases.insert(
        6, [5, 6, 7, 8])
    # phase Left. Southbound
    phases.insert(
        7, [4])
    # phase Through, Right. Northbound
    phases.insert(
        8, [11, 12, 13, 14])

    right_turns = [
        0, 5, 11, 16]
    next_signals = list(
        "rrrrrrrrrrrrrrrrrrrrrr")  # init signals

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
        # Check if a yellow phase is needed
        if current_signals[x] == 'G' and next_signals[x] == 'r':
            yellow_phase = True

    if yellow_phase:
        for x in range(len(current_signals)):
            # If a yellow phase is needed then find which lanes
            if current_signals[x] == 'G' and next_signals[x] == 'r':
                                                                   # should be assigned yellow
                current_signals[x] = 'y'
        traci.trafficlights.setRedYellowGreenState(
            "gneJ1", ''.join(current_signals))
        return False
    else:
        traci.trafficlights.setRedYellowGreenState(
            "gneJ1", ''.join(next_signals))
        return True


def run():

    # for i in range(30):

    # Load the demand file
    with open('State_Street_4500_South.txt', 'r') as fp:
        demand = fp.readlines()

    demand.pop(
        0)
    # The two first entries are the file header, depose them
    demand.pop(
        0)

    # Vehicles dynamic count
    vehNr = 0
    # N = 57600  # number of time steps (seconds) total 16 hours
    # number of time steps (seconds) total 16 hours
    N = 30 * \
        300

    # The last time the signals have changed
    last_phase_change = 0
    # currently green phases index
    current_phase = [
        2, 6]
    # indicates whether the current phase is yellow
    yellow = False

    # The +300 is to allow all vehicles (generated up to time N) to clear the network
    while int(traci.simulation.getCurrentTime()*0.001) < N + 300:
        vehicles = vehicle_generator(int(
            traci.simulation.getCurrentTime()*0.001), demand)
        for v in vehicles:
            traci.vehicle.add(str(
                vehNr), v[0], typeID=v[1])
            vehNr += 1
        if int(traci.simulation.getCurrentTime()*0.001) - last_phase_change >= min_phase_time:
            if yellow:
                next_phase = current_phase
            else:
                # Logic for picking the next phase
                # Next phase is a list of int representing the phases that should be assigned green next according to:
                #  6: Through, Right. Westbound
                #  2: Through, Right. Eastbound
                #  8: Through, Right. Northbound
                #  4: Through, Right. Southbound

                #  1: Left. Westbound
                #  5: Left. Eastbound
                #  3: Left. Northbound
                #  7: Left. Southbound

                # If no change is required for the current signal assignment then return -1 (instead of a list of int)
                next_phase = logic.get_phase(
                    current_phase)

                if next_phase == -1:
                    next_phase = current_phase

                # print(int(traci.simulation.getCurrentTime()*0.001), last_phase_change, next_phase)
            if next_phase != -1:  # If a phase change is required
                # chosen phases index
                current_phase = next_phase
                print(int(
                    traci.simulation.getCurrentTime()*0.001), next_phase)
                # If the chosen phases are applicable (no yellow transition is required)
                if set_phase(next_phase):
                    yellow = False
                else:
                    yellow = True
                last_phase_change = int(
                    traci.simulation.getCurrentTime()*0.001)
        traci.simulationStep()

    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary(
            'sumo')
    else:
        sumoBinary = checkBinary(
            'sumo-gui')
    # sumoBinary = checkBinary('sumo')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", "Data/State_Street_4500_South.sumocfg", "--tripinfo-output",
                 "tripinfo.xml"])  # ,  "--time-to-teleport -1"
    run()
