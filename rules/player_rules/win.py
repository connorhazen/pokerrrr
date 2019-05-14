# coding: utf-8

from rules.player_rules.base import PlayerRulesBase


class WinRule(PlayerRulesBase):
    def __init__(self):
        super(WinRule, self).__init__()

    def condition(self, player):
        if not player.cards_in_hand:
            player.win_total_cnt += 1
            return True
        return False
