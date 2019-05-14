# coding: utf-8

from state.player_state.base import PlayerStateBase
from state.player_state.double import DoubleState
from state.player_state.wait import WaitState
#from rules.player_rules.manager import PlayerRulesManager

class RobState(PlayerStateBase):
    def __init__(self):
        super(RobState, self).__init__()

    def next_state(self, owner):
        if owner.table.conf.has_double:
            owner.machine.trigger(DoubleState())
            owner.table.machine.cur_state.execute(owner.table, "skip_double")
        else:
            owner.machine.trigger(WaitState())
            owner.table.machine.cur_state.execute(owner.table, "skip_step")

    def execute(self, owner, event, proto=None):
        super(RobState, self).execute(owner, event, proto)
        from logic.player_action import rob_dealer, rob_dealer_happy, rob_skip
        if event == "rob_dealer":
            rob_dealer(owner, proto)
        elif event == "rob_dealer_happy":
            rob_dealer_happy(owner, proto)            
        elif event == "rob_skip":
            rob_skip(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
