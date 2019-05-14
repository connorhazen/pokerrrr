# coding: utf-8

from state.player_state.base import PlayerStateBase
from state.table_state.wait import WaitState
from state.player_state.discard import DiscardState


class ShowCardState(PlayerStateBase):
    def __init__(self):
        super(ShowCardState, self).__init__()

    def next_state(self, owner):
        # 明牌之后出牌
        owner.table.machine.trigger(WaitState())
        owner.machine.trigger(DiscardState())


    def execute(self, owner, event, proto=None):
        super(ShowCardState, self).execute(owner, event, proto)
        from logic.player_action import show_card
        if event == "show_card":
            show_card(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
