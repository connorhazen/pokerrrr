# coding: utf-8

from rules.table_rules.base import TableRulesBase
from state.table_state.dealer_choose import DealerChooseState


class DealerChooseRule(TableRulesBase):
    def condition(self, table):
        if table.dealer_seat == table.spy_chair:
            return True
        else:
            return False

    def action(self, table):
        # table.machine.trigger(SettleForRoomState())
        # table.dismiss_room()
        from state.player_state.dealer_choose import DealerChooseState as player_DealerChooseState
        table.seat_dict[table.dealer_seat].machine.trigger(player_DealerChooseState())
        table.machine.trigger(DealerChooseState())
