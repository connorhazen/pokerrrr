# coding: utf-8
import time

from tornado.ioloop import IOLoop

from logic.player_action import dealer_choose
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from rules.define import PLAYER_RULE_CHOOSE
from state.table_state.base import TableStateBase
from settings import choose_delay


class DealerChooseState(TableStateBase):
    def __init__(self):
        super(DealerChooseState, self).__init__()

    def enter(self, owner):
        super(DealerChooseState, self).enter(owner)
        # 初始化阵营
        owner.init_camp()
        if owner.dealer_seat == owner.spy_chair:
            proto = game_pb2.PokerDealerChooseInitResponse()
            proto.dealer_seat = owner.dealer_seat
            for e_player in owner.player_dict.values():
                proto.flag = -1
                if e_player.seat == owner.dealer_seat:
                    # 只给地主返回是否拿了狗腿8，其他玩家返回-1
                    # proto.flag = 1 if owner.dealer_seat == owner.spy_chair else -1
                    proto.flag = 1
                send(POKER_DEALER_CHOOSE_INIT, proto, e_player.session)
        else:
            from rules.player_rules.manager import PlayerRulesManager
            for player in owner.player_dict.values():
                PlayerRulesManager().condition(player, PLAYER_RULE_CHOOSE)
        # 计时器控制时间，中间的所有请求都可以接收，这个时间是控制死必须延迟这个时间
        # 2018.5.17取消计时器
        # owner.choose_begin_time = time.time()
        # owner.temp_timer = IOLoop().instance().add_timeout(owner.choose_begin_time + choose_delay, self.after_delay,
        #                                                    owner)

        owner.dumps()

    def after_delay(self, owner):
        # 取消计时器之后这个方法就不会走了
        if owner.temp_timer:
            IOLoop().instance().remove_timeout(owner.temp_timer)
            owner.temp_timer = None
        if owner.dealer_seat == owner.spy_chair:
            # 默认叫狗腿
            dealer = owner.seat_dict[owner.dealer_seat]
            proto_req = game_pb2.PokerDealerChooseRequest()
            proto_req.choose_code = 2
            dealer_choose(dealer, proto_req)
        # 只有指定狗腿时返回
        if owner.spy_card != "8G":
            proto_res = game_pb2.PokerDealerChooseResponse()
            proto_res.choose_code = 2
            proto_res.spy_card = owner.spy_card
            owner.replay["procedure"].append({"change_goutui": owner.spy_card})
            for e_player in owner.player_dict.values():
                send(POKER_DEALER_CHOOSE, proto_res, e_player.session)
        from rules.player_rules.manager import PlayerRulesManager
        for player in owner.player_dict.values():
            PlayerRulesManager().condition(player, PLAYER_RULE_CHOOSE)

    def execute(self, owner, event):
        super(DealerChooseState, self).execute(owner, event)
        from logic.table_action import skip_step
        # if event == "skip_show_card":
        #     skip_show_card(owner)
        if event == "skip_step":
            skip_step(owner)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
