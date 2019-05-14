# coding: utf-8
from protocol import game_pb2
from protocol.commands import SHOWCARD_DEALER
from protocol.serialize import send

from state.player_state.base import PlayerStateBase
from state.player_state.wait import WaitState


class ShowCardDealerState(PlayerStateBase):
    def __init__(self):
        super(ShowCardDealerState, self).__init__()

    def enter(self, owner):
        super(ShowCardDealerState, self).enter(owner)

        proto = game_pb2.ShowCardDealerResponse()
        send(SHOWCARD_DEALER, proto, owner.session)
        owner.dumps()
    def next_state(self, owner):
        owner.machine.trigger(WaitState())
        owner.table.machine.cur_state.execute(owner.table, "skip_step")

    def execute(self, owner, event, proto=None):
        super(ShowCardDealerState, self).execute(owner, event, proto)
        from logic.player_action import show_card_dealer
        if event == "show_card_dealer":
            show_card_dealer(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
