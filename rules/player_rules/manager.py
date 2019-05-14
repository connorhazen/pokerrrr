# coding: utf-8
from rules.define import *
from utils.singleton import Singleton
from state.table_state.end import EndState
from state.player_state.prompt import PromptState


class PlayerRulesManager(object):
    __metaclass__ = Singleton

    def __init__(self):
        from rules.player_rules.win import WinRule
        self.rules = {
            PLAYER_RULE_READY: [],
            PLAYER_RULE_DRAW: [],
            PLAYER_RULE_DISCARD: [],
            PLAYER_RULE_DEAL: [],
            PLAYER_RULE_ROB: [],
            PLAYER_RULE_SHOWCARD: [],
            PLAYER_RULE_SHOWCARD_DEALER: [],
            PLAYER_RULE_DOUBLE: [],
            PLAYER_RULE_CHOOSE: [],
            PLAYER_RULE_WIN: [WinRule()],

        }

    def condition(self, player, rule):
        if rule not in self.rules.keys():
            player.table.logger.warn("player {0} rule {1} not exist".format(player.seat, rule))
            return
        flag = False
        for r in self.rules[rule]:
            if r.condition(player):
                flag = True
        if flag:
            if rule in [PLAYER_RULE_WIN]:
                player.table.machine.trigger(EndState())
            else:
                player.machine.trigger(PromptState())
        else:
            player.machine.cur_state.next_state(player)
