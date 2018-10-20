#!/usr/bin/env python

import sys
import os
import optparse
import subprocess
import random
import traci
from Logic import Logic

#  Learning agent timing logic


class LogicRL(Logic):

    # get_phase: return a list of phase indices (to be set to green) or -1 if no change is required
    #  6: Through, Right. Westbound
    #  2: Through, Right. Eastbound
    #  8: Through, Right. Northbound
    #  4: Through, Right. Southbound

    #  1: Left. Westbound
    #  5: Left. Eastbound
    #  3: Left. Northbound
    #  7: Left. Southbound
    def get_phase(self, current_phases):
        if self.left_policy == "protected-permissive":
            # TODO: your code here
            table_prot_perm = [[1, 5], [1, 5, 2, 6], [3, 7], [3, 7, 4, 8]]

            # next state:
            if need_change:
                next_index = (table_prot_perm.index(current_phases) + 1) % 4
                return table_prot_perm[next_index]
            else:
                return -1

        else:
            raise NotImplementedError
