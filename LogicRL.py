#!/usr/bin/env python

import sys
import os
import optparse
import subprocess
import random
import traci
from Logic import Logic
from DeepLearningPython35.network import Network
import numpy as np


class LogicRL(Logic):
    def __init__(self, left_policy):
        Logic.__init__(
            self, left_policy)
        self.dql = Network(
            [23, 50, 1])
        # self.dql.load(
        #     './neuron/weight_7000.npy', './neuron/bias_7000.npy')
        self.dql.load(
            './new_neuron/weight_500.npy', './new_neuron/bias_500.npy')

    def Q_val(self, current_phase, action):
        cur_state = self.get_state(
            current_phase)

        return np.max(self.dql.feedforward(cur_state+[action, 1]))

    def get_action(self, current_phase):
        # return the action with highest q value
        cur_state = self.get_state(
            current_phase)
        action = self.dql.get_action(
            cur_state)
        return action

    def get_phase(self, current_phase):
        if self.left_policy == "protected-permissive":
            # TODO: your code here
            cur_state = self.get_state(
                current_phase)
            action = self.dql.get_action(
                cur_state)
            return self.act_lights(action, current_phase)
        else:
            raise NotImplementedError

    def get_state(self, current_phase):
        # the state of Q function:
        # s = (a, jamlength for all lanes): a is integer of {0,1,2,3} for 4 rings
        getID = {0: 'S0', 1: 'S1', 2: 'S2', 3: 'S3', 4: 'S4', 5: 'W0', 7: 'W1', 8: 'W2', 9: 'W3', 10: 'W4',
                 11: 'N0', 12: 'N1', 13: 'N2', 14: 'N3', 15: 'N4', 16: 'E0', 18: 'E1', 19: 'E2', 20: 'E3', 21: 'E4'}
        lane_jam = []
        for i in getID:
            lane = 'laneAreaDetector.' + \
                getID[i]
            # lane_jam.append(traci.areal.getJamLengthVehicle(lane))
            # lane_jam.append(traci.areal.getLastStepVehicleNumber(lane))
            lane_jam.append(
                traci.areal.getLastStepMeanSpeed(lane))
        table_prot_perm = [[1, 5], [
            1, 5, 2, 6], [3, 7], [3, 7, 4, 8]]
        try:
            light_info = [
                table_prot_perm.index(current_phase)]
        except:
            light_info = [
                0]
        return light_info+lane_jam

    def act_lights(self, action, current_phase):
        # action from the NN is 0 & 1, where 1 is move to next ring, 0 is stay current light
        if action == 0:
            return -1
        elif action == 1:
            table_prot_perm = [[1, 5], [
                1, 5, 2, 6], [3, 7], [3, 7, 4, 8]]
            try:
                next_index = (table_prot_perm.index(
                    current_phase) + 1) % 4
            except:
                next_index = 0
            return table_prot_perm[next_index]
