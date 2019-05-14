# coding: utf-8


from rules.define import *
from rules.table_rules.manager import TableRulesManager
# from state.player_state.draw import DrawState
from state.player_state.discard import DiscardState
from state.table_state.base import TableStateBase
from state.table_state.wait import WaitState
from state.player_state.show_card import ShowCardState as PlayerShowCardState
from state.table_state.show_card import ShowCardState as TableShowCardState


class StepState(TableStateBase):
    def __init__(self):
        super(StepState, self).__init__()

    def enter(self, owner):
        super(StepState, self).enter(owner)
        TableRulesManager().condition(owner, TABLE_RULE_STEP)

    def next_state(self, owner):
        if owner.active_seat >= 0:
            active_player = owner.seat_dict[owner.active_seat]
            owner.active_seat = active_player.next_seat
        else:
            owner.active_seat = owner.dealer_seat
        active_player = owner.seat_dict[owner.active_seat]

        if active_player.has_chosen_ming:
            # 出牌
            owner.machine.trigger(WaitState())
            active_player.machine.trigger(DiscardState())
        else:
            # 明牌
            active_player.machine.trigger(PlayerShowCardState())
            owner.machine.trigger(TableShowCardState())
