# coding: utf-8
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from state.table_state.base import TableStateBase


class DoubleState(TableStateBase):
    def __init__(self):
        super(DoubleState, self).__init__()

    def enter(self, owner):
        super(DoubleState, self).enter(owner)
        proto = game_pb2.PokerDoubleInitResponse()
        for k, v in owner.seat_dict.iteritems():
            if k != owner.dealer_seat:
                proto.double_list.append(k)

        for k, v in owner.seat_dict.iteritems():
            send(POKER_DOUBLE_INIT, proto, v.session)
        owner.dumps()
    def execute(self, owner, event):
        super(DoubleState, self).execute(owner, event)
        from logic.table_action import skip_step
        if event == "skip_step":
            skip_step(owner)            