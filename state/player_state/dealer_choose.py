# coding: utf-8

from state.player_state.base import PlayerStateBase
from state.player_state.wait import WaitState



class DealerChooseState(PlayerStateBase):
    def __init__(self):
        super(DealerChooseState, self).__init__()

    def next_state(self, owner):
        # owner.machine.trigger(ShowCardState())
        # owner.table.machine.cur_state.execute(owner.table, "skip_show_card")
        # 2018.5.9改明牌之后出牌
        owner.machine.trigger(WaitState())
        owner.table.machine.cur_state.execute(owner.table, "skip_step")

    def execute(self, owner, event, proto=None):
        super(DealerChooseState, self).execute(owner, event, proto)
        from logic.player_action import dealer_choose
        if event == "dealer_choose":
            dealer_choose(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
