# coding: utf-8

from state.player_state.base import PlayerStateBase
from state.player_state.show_card_dealer import ShowCardDealerState
from state.player_state.wait import WaitState


#from rules.player_rules.manager import PlayerRulesManager

class DoubleState(PlayerStateBase):
    def __init__(self):
        super(DoubleState, self).__init__()

    def next_state(self, owner):
        # 地主在翻倍后还有一次明牌机会
        if owner.table.conf.has_show and owner.table.dealer_seat == owner.seat and owner.show_card != 2:
            owner.machine.trigger(ShowCardDealerState())
            return 
        owner.machine.trigger(WaitState())
        owner.table.machine.cur_state.execute(owner.table, "skip_step")

    def execute(self, owner, event, proto=None):
        super(DoubleState, self).execute(owner, event, proto)
        from logic.player_action import double, skip_wait
        if event == "poker_double":
            double(owner, proto)
        elif event == "skip_wait":
            skip_wait(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
