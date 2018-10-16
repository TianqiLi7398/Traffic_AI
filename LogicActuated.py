#!/usr/bin/env python

import sys
import os
import optparse
import subprocess
import random
import traci
from Logic import Logic


#  Actuated timing logic
class LogicActuated(Logic):

    # get_phase: return a list of phase indices (to be set to green) or -1 if no change is required
    #  6: Through, Right. Westbound
    #  2: Through, Right. Eastbound
    #  8: Through, Right. Northbound
    #  4: Through, Right. Southbound

    #  1: Left. Westbound
    #  5: Left. Eastbound
    #  3: Left. Northbound
    #  7: Left. Southbound
    def __init__(self, left_policy):
        Logic.__init__(self, left_policy)
        self.phases = [[],
                       [9, 10],
                       [16, 17, 18, 19],
                       [15],
                       [0, 1, 2, 3],
                       [20, 21],
                       [5, 6, 7, 8],
                       [4],
                       [11, 12, 13, 14]]
        self.table_protected = [[1, 5], [2, 6], [3, 7], [4, 8]]
        self.table_prot_perm = [[1, 5, 2, 6], [3, 7, 4, 8]]
        self.ns_dir, self.ew_dir = {'left': [1, 5], 'through': [6, 2]}, {
            'left': [3, 7], 'through': [4, 8]}
        self.left_table = [1, 5, 3, 7]
        self.through_table = [6, 2, 8, 4]
        self.direction_threshold = 10
        self.permissive_threshold = 20
        self.protect_threshold = 3  # if in protect mode, change to left/through threshold
        self.getID = {0: 'S0', 1: 'S1', 2: 'S2', 3: 'S3', 4: 'S4', 5: 'W0', 7: 'W1', 8: 'W2', 9: 'W3', 10: 'W4',
                      11: 'N0', 12: 'N1', 13: 'N2', 14: 'N3', 15: 'N4', 16: 'E0', 18: 'E1', 19: 'E2', 20: 'E3', 21: 'E4'}

    def get_phase(self, current_phases):
        # TODO: your code here
        # phases = [[],
        #           [9, 10],
        #           [16, 17, 18, 19],
        #           [15],
        #           [0, 1, 2, 3],
        #           [20, 21],
        #           [5, 6, 7, 8],
        #           [4],
        #           [11, 12, 13, 14]]
        # table_protected = [[1, 5], [2, 6], [3, 7], [4, 8]]
        # table_prot_perm = [[1, 5, 2, 6], [3, 7, 4, 8]]
        # ns_dir, ew_dir = {'left': [1, 5], 'through': [6, 2]}, {'left': [3, 7], 'through': [4, 8]}
        # left_table = [1, 5, 3, 7]
        # through_table = [6, 2, 8, 4]

        # analyze current direction
        if current_phases[0] in self.through_table:
            if current_phases[0] in self.ns_dir['through']:
                # current in ns direction
                current_dir, opposite_dir = self.ns_dir, self.ew_dir
            else:
                current_dir, opposite_dir = self.ew_dir, self.ns_dir
        else:
            if current_phases[0] in self.ns_dir['left']:
                current_dir, opposite_dir = self.ns_dir, self.ew_dir
            else:
                current_dir, opposite_dir = self.ew_dir, self.ns_dir

        # check the mode
        if current_phases in self.left_table:
            cur_mode = ['left']
        elif current_phases in self.through_table:
            cur_mode = ['through']
        else:
            cur_mode = ['left', 'through']

        # check if need change mode
        need_change_dir, new_green_lights = self.check_mode(
            cur_mode, current_dir, opposite_dir)

        return new_green_lights

    def check_mode(self, cur_mode, current_dir, opposite_dir):
        # gather all waiting vehicles in opposite_dir
        oppo_lane_thr, oppo_lane_left, cur_lane_thr, cur_lane_left = [], [], [], []
        veh_cur_thr, veh_cur_left, veh_opp_thr, veh_opp_left = 0, 0, 0, 0

        for i in opposite_dir['through']:
            oppo_lane_thr += self.phases[i]

        for i in opposite_dir['left']:
            oppo_lane_left += self.phases[i]

        for i in current_dir['through']:
            cur_lane_thr += self.phases[i]

        for i in current_dir['left']:
            cur_lane_left += self.phases[i]

        # get all directions

        for lane in oppo_lane_thr:
            try:
                lane = 'laneAreaDetector.' + self.getID[lane]
                # getJamLengthVehicle(lane)
                veh_opp_thr += traci.areal.getJamLengthVehicle(lane)
            except KeyError:
                continue  # two right turns
        for lane in oppo_lane_left:
            try:
                lane = 'laneAreaDetector.' + self.getID[lane]
                veh_opp_left += traci.areal.getJamLengthVehicle(lane)
            except KeyError:
                continue  # two right turns

        for lane in cur_lane_thr:
            try:
                lane = 'laneAreaDetector.' + self.getID[lane]
                veh_cur_thr += traci.areal.getJamLengthVehicle(lane)
            except KeyError:
                continue  # two right turns

        for lane in cur_lane_left:
            try:
                lane = 'laneAreaDetector.' + self.getID[lane]
                veh_cur_left += traci.areal.getJamLengthVehicle(lane)
            except KeyError:
                continue  # two right turns

        if veh_opp_left + veh_opp_thr - veh_cur_thr-veh_cur_left > self.direction_threshold:
            # change direction，but first find which is the heavist traffic
            if veh_opp_thr > veh_opp_left:
                return True, opposite_dir['through']
            elif veh_opp_thr < veh_opp_left:
                return True, opposite_dir['left']
            else:
                return True, opposite_dir['through'] + opposite_dir['left']
        else:
            if len(cur_mode) == 2:
                # in permissive mode
                if veh_cur_thr - veh_cur_left > self.permissive_threshold:
                    # too much through veh, should get to protect mode
                    return False, current_dir['through']
                elif veh_cur_left - veh_cur_thr > self.permissive_threshold:
                    # too much left veh, should get to protect mode
                    return False, current_dir['left']
                else:
                    return False, -1
            else:
                # decide if need go permissive mode
                if abs(veh_cur_thr - veh_cur_left) < self.permissive_threshold:
                    return False, current_dir['through']+current_dir['left']
                else:
                    return False, -1
