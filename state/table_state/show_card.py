# coding: utf-8

from tornado.ioloop import IOLoop

from protocol import game_pb2
from protocol.commands import POKER_SHOW_CARDS_INIT, POKER_SHOW_CARDS_RESULT
from protocol.serialize import send
from state.table_state.base import TableStateBase
from state.table_state.wait import WaitState
from state.player_state.discard import DiscardState


class ShowCardState(TableStateBase):
    def __init__(self):
        super(ShowCardState, self).__init__()

    def enter(self, owner):
        super(ShowCardState, self).enter(owner)
        # 考虑到重启之后的问题，有可能这里出现问题
        if not owner.seat_dict[owner.dealer_seat].has_chosen_ming:
            # 地主没进行选择
            owner.show_card_seat = owner.dealer_seat
            proto = game_pb2.PokerShowCardInitResponse()
            proto.seat = owner.dealer_seat
            proto.flag = 1
            for player in owner.player_dict.values():
                send(POKER_SHOW_CARDS_INIT, proto, player.session)
            # owner.show_card_begin_time = time.time()
            # owner.temp_timer = IOLoop().instance().add_timeout(owner.show_card_begin_time + show_card_delay,
            #                                                    self.show_step2, owner)
        else:
            owner.show_card_seat = owner.dealer_seat
            all_player_has_chose = True
            for i in range(owner.chairs):
                show_card_player = owner.seat_dict[owner.show_card_seat]
                if not show_card_player.has_chosen_ming:
                    all_player_has_chose = False
                    break
                owner.show_card_seat = show_card_player.next_seat
            if all_player_has_chose:
                # 所有人都选择过明牌
                self.temp(owner)
            else:
                if owner.temp_timer:
                    IOLoop().instance().remove_timeout(owner.temp_timer)
                    owner.temp_timer = None
                proto = game_pb2.PokerShowCardInitResponse()
                proto.seat = owner.show_card_seat
                proto.flag = owner.get_show_cards_flag(owner.show_card_seat)
                for player in owner.player_dict.values():
                    send(POKER_SHOW_CARDS_INIT, proto, player.session)
                # owner.show_card_begin_time = time.time()
                # owner.temp_timer = IOLoop().instance().add_timeout(owner.show_card_begin_time + show_card_delay,
                #                                                    self.show_step2, owner)
        owner.dumps()

    def show_step2(self, owner):
        if owner.temp_timer:
            IOLoop().instance().remove_timeout(owner.temp_timer)
            owner.temp_timer = None
        last_show_player = owner.seat_dict[owner.show_card_seat]
        # 超时未进行选择默认不明牌,取消计时器之后这段代码怕是不会走了
        if not last_show_player.has_chosen_ming:
            proto_req = game_pb2.PokerShowCardRequest()
            proto_req.flag = 2
            from logic.player_action import show_card
            show_card(last_show_player, proto_req)

        # 发给前端明牌结果
        proto_show_res = game_pb2.PokerShowCardResponse()
        proto_show_res.seat = owner.show_card_seat
        if last_show_player.show_card == 1:
            # 明牌发现狗腿直接暴露
            if owner.spy_card in last_show_player.cards_in_hand and last_show_player.seat != owner.dealer_seat:
                owner.notify_goutui()
        for card in last_show_player.cards_in_hand:
            show_card = proto_show_res.show_cards.add()
            # 如果明牌就返回真实牌型,否则返回空字符串
            show_card.card = card if last_show_player.show_card == 1 else ""
        for e_player in owner.player_dict.values():
            send(POKER_SHOW_CARDS_RESULT, proto_show_res, e_player.session)

        # 接下来就是各种骚操作看好了！
        from rules.player_rules.manager import PlayerRulesManager
        from rules.define import PLAYER_RULE_SHOWCARD
        PlayerRulesManager().condition(last_show_player, PLAYER_RULE_SHOWCARD)

        # 获取下一个要明牌位置
        # owner.show_card_seat = owner.seat_dict[owner.show_card_seat].next_seat
        # if owner.seat_dict[owner.show_card_seat].has_chosen_ming:
        #     self.temp(owner)
        #     return
        # proto = game_pb2.PokerShowCardInitResponse()
        # proto.seat = owner.show_card_seat
        # proto.flag = owner.get_show_cards_flag(owner.show_card_seat)
        # for player in owner.player_dict.values():
        #     send(POKER_SHOW_CARDS_INIT, proto, player.session)
        # owner.show_card_begin_time = time.time()
        # owner.temp_timer = IOLoop().instance().add_timeout(owner.show_card_begin_time + show_card_delay,
        #                                                    self.show_step2, owner)

    def temp(self, owner):
        if owner.temp_timer:
            IOLoop().instance().remove_timeout(owner.temp_timer)
            owner.temp_timer = None
        owner.show_card_begin_time = 0
        # from rules.player_rules.manager import PlayerRulesManager
        # for player in owner.player_dict.values():
        #     PlayerRulesManager().condition(player, PLAYER_RULE_SHOWCARD)
        # 到这是因为关服时机错误，将最后一个玩家推到discard状态
        owner.machine.trigger(WaitState())
        owner.seat_dict[owner.active_seat].machine.trigger(DiscardState())

    def execute(self, owner, event):
        super(ShowCardState, self).execute(owner, event)
        # from logic.table_action import skip_step
        # if event == "skip_step":
        #     skip_step(owner)
        if event == "player_show_step":
            self.show_step2(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
