# coding: utf-8

from state.player_state.base import PlayerStateBase


class SettleState(PlayerStateBase):

    def execute(self, owner, event, proto=None):
        super(SettleState, self).execute(owner, event, proto)
        if event == "ready":
            owner.ready()
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
