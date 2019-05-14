# coding: utf-8
from copy import copy

from state.player_state.base import PlayerStateBase
from logic.player_action import discard
from state.player_state.wait import WaitState
from protocol.commands import NOTIFY_DISCARD
from protocol import game_pb2


class DiscardState(PlayerStateBase):
    def enter(self, owner):
        super(DiscardState, self).enter(owner)
        # 防止前端未发 pass
        owner.table.clear_prompt()
        owner.table.clear_actions()
        proto = game_pb2.PokerDiscardNotifyResponse()
        proto.player = owner.uuid
        owner.table.reset_proto(NOTIFY_DISCARD)
        for player in owner.table.player_dict.values():
            player.proto.p = copy(proto)
            player.proto.send()
        owner.dumps()
               
    def execute(self, owner, event, proto=None):
        super(DiscardState, self).execute(owner, event, proto)
        if event == "discard":
            discard(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))

    def exit(self, owner):
        super(DiscardState, self).exit(owner)

    def next_state(self, owner):
        owner.machine.trigger(WaitState())
        owner.table.machine.cur_state.execute(owner.table, "step")
