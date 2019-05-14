# coding: utf-8

from rules.table_rules.base import TableRulesBase
# from state.table_state.settle_for_room import SettleForRoomState


class SettleForRoundRule(TableRulesBase):
    def condition(self, table):
        if table.cur_round > table.conf.max_rounds:
            return True
        else:
            return False

    def action(self, table):
        # table.machine.trigger(SettleForRoomState())
        table.dismiss_room()
