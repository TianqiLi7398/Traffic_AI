#!/usr/bin/env python

import sys
import optparse
import subprocess
import random
import traci
from Logic import Logic


#  Fixed timing logic
class LogicFixed(Logic):

    # get_phase: return a list of phase indices (to be set to green) or -1 if no change is required
    #  6: Through, Right. Westbound
    #  2: Through, Right. Eastbound
    #  8: Through, Right. Northbound
    #  4: Through, Right. Southbound

    #  1: Left. Westbound
    #  5: Left. Eastbound
    #  3: Left. Northbound
    #  7: Left. Southbound
    def get_phase(self, current_phases, a, b, c):
        if self.left_policy == "protected":
            return self.protected(current_phases, a, b, c)
        elif self.left_policy == "protected-permissive":
            return self.protected_permissive(current_phases, a, b, c)
        elif self.left_policy == "split-protect-NS":
            return self.splitNS(current_phases, a, b, c)
        elif self.left_policy == "split-protect-EW":
            return self.splitEW(current_phases, a, b, c)
        elif self.left_policy == "unrestricted":
            # Fixed time requires a defined phase sequence
            raise NotImplementedError

    def protected(self, current_phases, a, b, c):
        # TODO: your code here
        table_protected = [[1, 5], [2, 6], [3, 7], [4, 8]]  # order for table_protected
        # a, b, c, d = 25, 25, 25, 25
        time_inverval = [0, a*3, (a+b)*3, (a+b+c)*3]
        period_time = int(traci.simulation.getCurrentTime()*0.001) % 300
        need_change = [time_inverval.index(i) for i in time_inverval if i == period_time]

        if need_change != []:
            return table_protected[need_change[0]]
        else:
            return -1

    def protected_permissive(self, current_phases, a, b, c):
        # TODO: your code here
        table_prot_perm = [[1, 5], [1, 5, 2, 6], [3, 7], [
            3, 7, 4, 8]]  # order for protected_permissive

        time_inverval = [0, a*3, (a+b)*3, (a+b+c)*3]
        period_time = int(traci.simulation.getCurrentTime()*0.001) % 300
        need_change = [time_inverval.index(i) for i in time_inverval if i == period_time]

        if need_change != []:
            return table_prot_perm[need_change[0]]
        else:
            return -1

    def splitNS(self, current_phases,  a, b, c):
        # TODO: your code here
        table_split_NS = [[1, 5], [1, 5, 2, 6], [4, 7], [3, 8]]  # order for splitNS
        time_inverval = [0, a*3, (a+b)*3, (a+b+c)*3]  # time to change
        period_time = int(traci.simulation.getCurrentTime()*0.001) % 300
        need_change = [time_inverval.index(i) for i in time_inverval if i == period_time]

        if need_change != []:
            return table_split_NS[need_change[0]]
        else:
            return -1

    def splitEW(self, current_phases, a, b, c):
        # TODO: your code here
        table_split_EW = [[3, 7], [4, 7, 3, 8], [1, 6], [2, 5]]  # order for splitEW
        time_inverval = [0, a*3, (a+b)*3, (a+b+c)*3]  # time to change
        period_time = int(traci.simulation.getCurrentTime()*0.001) % 300
        need_change = [time_inverval.index(i) for i in time_inverval if i == period_time]

        if need_change != []:
            return table_split_EW[need_change[0]]
        else:
            return -1
