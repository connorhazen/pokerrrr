# coding: utf-8

from rules.define import *
from rules.player_rules.manager import PlayerRulesManager
from state.player_state.base import PlayerStateBase
from state.player_state.dealer_choose import DealerChooseState
from state.player_state.rob import RobState
from state.player_state.show_card import ShowCardState
from protocol.serialize import send
from protocol.commands import *
from protocol import game_pb2
from state.player_state.wait import WaitState


class DealState(PlayerStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)

        PlayerRulesManager().condition(owner, PLAYER_RULE_DEAL)
        owner.dumps()



    def next_state(self, owner):
        owner.proto.send()
        # 这里跳转到choose状态
        owner.machine.trigger(DealerChooseState())
        owner.table.machine.cur_state.execute(owner.table, "skip_choose")
        


