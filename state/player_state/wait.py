# coding: utf-8
from logic.player_action import other_discard
from state.player_state.base import PlayerStateBase


class WaitState(PlayerStateBase):

    def next_state(self, owner):
        owner.machine.trigger(self)

    def execute(self, owner, event, proto=None):
        super(WaitState, self).execute(owner, event, proto)
        if event == "other_discard":
            other_discard(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
