# coding: utf-8

import json
import time
import types
import weakref

from copy import copy
from tornado.ioloop import IOLoop

from logic.player_proto_mgr import PlayerProtoMgr
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from settings import redis, dismiss_delay
from state.machine import Machine
from state.player_state.ready import ReadyState
from state.status import table_state_code_map, player_state_code_map


class Player(object):
    def __init__(self, uuid, info, session, table):
        super(Player, self).__init__()
        self.uuid = uuid
        self.table = weakref.proxy(table)
        self.info = info
        self.seat = None
        self.prev_seat = None
        self.next_seat = None
        self.session = session
        self.is_online = True
        self.state = None
        self.vote_state = None
        self.vote_timer = None
        self.status = 0
        self.event = None

        self.machine = None
        Machine(self)

        self.score = 0
        self.total = 0
        self.win_total_cnt = 0  # 赢牌次数
        self.is_owner = 0

        self.cards_discard = []
        self.last_cards_discard = []

        self.win_type = 0
        self.win_flags = []

        self.prompts = 0
        # 提示ID
        self.prompt_id = 0
        # 动作
        self.action_dict = {}
        self.action_id = 0
        self.action_weight = 0
        self.action_rule = None
        self.action_ref_cards = None
        self.action_op_card = None

        # 手牌 
        self.cards_in_hand = []
        self.bomb_cnt = 0  # 炸弹次数
        # 本次叫地主
        self.rob_score = -1
        # 是否叫双倍
        self.double = 1
        # 是否明牌
        self.show_card = 0

        # 是否选择过明牌
        self.has_chosen_ming = False
        # 当局喜钱得分
        self.reward_points = 0
        # 总喜钱得分
        self.reward_total = 0
        # 总基础得分
        self.base_total = 0
        # 结算时计算手牌喜钱用到临时变量
        self.temp_reward_point = 0
        # 单局喜的个数
        self.reward_counts = 0
        self.proto = PlayerProtoMgr(self)

        self.boom_total = 0
        self.land_lord_times = 0

        # 用于构建活动额外数据
        self.ext = {}

    def dumps(self):
        data = {}
        for key, value in self.__dict__.items():
            if key == "table":
                data[key] = value.room_id
            elif key in ("session", "vote_timer"):
                continue
            elif key == "machine":
                data[key] = [None, None]
                if value.last_state:
                    data[key][0] = value.last_state.name
                if value.cur_state:
                    data[key][1] = value.cur_state.name
            elif key == "proto":
                val = self.proto.dump()
                if type(val) is types.StringType:
                    data[key] = unicode(val, errors='ignore')
                else:
                    data[key] = val
            else:
                if type(value) is types.StringType:
                    data[key] = unicode(value, errors='ignore')
                else:
                    data[key] = value
        # print "player", data
        redis.set("player:{0}".format(self.uuid), json.dumps(data))
        self.table.dumps()

    def delete(self):
        redis.delete("player:{0}".format(self.uuid))

    def add_prompt(self, prompt, rule, op_card, ref_cards=None):
        """
        提示包含以下字段信息
        规则（服务端自己持有）
        提示ID（客户端选择完后返回给服务器的ID， 这个字段是唯一的）
        提示类型
        操作牌（每一个提示都唯一对应一张操作牌， 由于关联牌的多样性，操作牌是可以重复的）
        关联牌（操作牌影响的相关牌，比如吃操作有N种吃法则，会有同一个操作牌对应N组关联牌）
        """
        if ref_cards is None:
            ref_cards = []
        self.prompts |= prompt
        self.prompt_id += 1
        self.action_dict[self.prompt_id] = {"rule": rule, "op_card": op_card, "ref_cards": ref_cards, "prompt": prompt}
        # print 'add prompt:',prompt

    def del_prompt(self):
        self.prompts = 0
        self.action_dict = {}
        self.prompt_id = 0

    # noinspection PyTypeChecker
    def highest_prompt_weight(self):
        max_weight = 0
        for i in self.action_dict.values():
            if i["prompt"] > max_weight:
                max_weight = i["prompt"]
        return max_weight

    def del_action(self):
        self.action_id = 0
        self.action_weight = 0
        self.action_rule = None
        self.action_ref_cards = None
        self.action_op_card = None

    def action(self, action_id):
        self.action_id = action_id
        action = self.action_dict[self.action_id]
        self.action_rule = action["rule"]
        self.action_weight = action["prompt"]
        self.action_ref_cards = action["ref_cards"]
        self.action_op_card = action["op_card"]
        # self.table.replay["procedure"].append([{"action": action, "seat": self.seat}])
        self.del_prompt()

    def clear_for_round(self):
        self.del_prompt()
        self.del_action()
        self.score = 0
        self.cards_in_hand = []
        self.cards_discard = []
        self.last_cards_discard = []
        self.cards_ready_hand = []

        self.win_type = 0
        self.win_flags = []
        # 斗地主
        self.bomb_cnt = 0
        self.rob_score = -1
        self.double = 1
        self.show_card = 0
        self.has_chosen_ming = False
        self.reward_points = 0
        self.temp_reward_point = 0
        self.reward_counts = 0
        self.dumps()

    def clear_for_room(self):
        self.clear_for_round()
        self.total = 0
        self.win_total_cnt = 0
        self.is_owner = 0
        self.reward_total = 0
        self.base_total = 0

    def online_status(self, status):
        self.is_online = status
        proto = game_pb2.OnlineStatusResponse()
        proto.player = self.uuid
        proto.status = self.is_online
        self.table.logger.info("player {0} toggle online status {1}".format(self.seat, status))
        for i in self.table.player_dict.values():
            if i.uuid == self.uuid:
                continue
            send(ONLINE_STATUS, proto, i.session)

    def reconnect(self):
        proto = game_pb2.PokerReconnectResponse()
        proto.room_id = self.table.room_id
        proto.kwargs = self.table.kwargs
        proto.owner = self.table.owner
        proto.room_score = self.table.get_base_core(self)
        proto.room_times = self.table.get_multiple(self)
        proto.room_status = int(table_state_code_map[self.table.state])
        proto.current_round = self.table.cur_round
        proto.active_seat = self.table.active_seat
        proto.spy_card = self.table.spy_card
        proto.spy_seat = -1
        if self.table.spy_chair != -1:
            if self.table.baolu:
                proto.spy_seat = self.table.spy_chair
        # proto.dealer = self.table.dealer_seat
        # active_seat = self.table.active_seat
        # print 'active seat:', active_seat,self.table.seat_dict[active_seat].state
        # 对于前端只有活动玩家处于出牌状态才发送指示灯
        # if active_seat >= 0 and self.table.seat_dict[active_seat].state == "WaitState" :
        #     proto.active_seat = self.table.active_seat
        # else:
        #     proto.active_seat = -1
        # print 'active seat:', proto.active_seat
        # proto.discard_seat = self.table.discard_seat
        # proto.rest_cards = self.table.cards_total if self.table.state == "InitState" else len(self.table.cards_on_desk)
        proto.code = 1
        if self.table.dealer_seat != -1:
            for card in self.table.cards_on_desk:
                cards = proto.rest_cards.add()
                cards.card = card

        log = {
            "description": "reconnect",
            "room_id": self.table.room_id,
            "kwargs": self.table.kwargs,
            "owner": self.table.owner,
            "owner_info": self.table.owner_info,
            "cur_round": self.table.cur_round,
            "room_status": table_state_code_map[self.table.state],
            "dealer": self.table.dealer_seat,
            "active_seat": self.table.active_seat,
            "discard_seat": self.table.discard_seat,
            "rest_cards": len(self.table.cards_on_desk),
            "code": 1,
            "room_score": self.table.get_base_core(self),
            "room_times": self.table.get_multiple(self),
            "current_round": self.table.cur_round,
            "spy_card":self.table.spy_card,
            "spy_seat":proto.spy_seat,
            "players": [],
        }

        for i in self.table.player_dict.values():
            player = proto.player.add()
            player.seat = i.seat
            player.player = i.uuid
            player.info = i.info
            player.status = player_state_code_map[i.state]
            player.is_online = 1 if i.is_online else 0
            player.total_score = i.total
            # 喜的个数
            player.bid_score = i.reward_counts
            # player.is_ting = i.isTing
            # player.is_jia = i.isJia
            # player.last_draw_card = self.draw_card
            # is_yao_fail:
            # is_yao_fail = 1
            # else:
            # is_yao_fail = 0

            for c in i.cards_in_hand:
                cards = player.cards_in_hand.add()
                if i.uuid == self.uuid:
                    cards.card = c
                elif i.show_card == 1:
                    cards.card = c
                else:
                    cards.card = ""
            for c in i.last_cards_discard:
                cards = player.cards_discard.add()
                cards.card = c
            if i.last_cards_discard:
                from algorithm.card_type.main import match_type
                player.cards_type = match_type(i.last_cards_discard, 10)
            if i.table.dealer_seat != -1:
                player.role = 1 if i.seat == i.table.dealer_seat else 0
                if proto.spy_seat != -1 and i.seat == proto.spy_seat:
                    player.role = 2
            else:
                player.role = -1
            # if len(self.table.farmer_double) <= 1:
            #     if self.seat in self.table.farmer_double:
            #         if i.seat == self.seat:
            #             # 自己是第一个农民
            #             player.has_double = i.double
            #         else:
            #             player.has_double = 0
            #     else:
            #         player.has_double = 0
            # else:
            #     player.has_double = i.double
            # 是否选择过明牌，在明牌阶段重连控制不出的显示
            player.has_double = 1 if i.has_chosen_ming else 0

            # 1明牌2不明牌0未选择
            player.has_show = i.show_card

            log["players"].append({
                "seat": i.seat,
                "player": i.uuid,
                "info": i.info,
                "status": player_state_code_map[i.state],
                "is_online": i.is_online,
                "total": i.total,
                "cards_in_hand": i.cards_in_hand,
                "cards_discard": i.cards_discard,
                "bid_score": i.reward_counts,
                "has_double": player.has_double,
                "has_show": i.show_card
            })
        send(POKER_RECONNECT, proto, self.session)
        self.table.logger.info(log)

        if self.table.dismiss_state:
            # 先弹出投票界面
            expire_seconds = int(dismiss_delay + self.table.dismiss_time - time.time())
            if expire_seconds <= 0:
                self.table.dismiss_room()
                return
            proto = game_pb2.SponsorVoteResponse()
            proto.room_id = self.table.room_id
            proto.sponsor = self.table.dismiss_sponsor
            proto.expire_seconds = expire_seconds
            send(SPONSOR_VOTE, proto, self.session)
            # 生成定时器
            if not self.vote_timer and self.uuid != self.table.dismiss_sponsor and not self.vote_state:
                proto_vote = game_pb2.PlayerVoteRequest()
                proto_vote.flag = True
                self.vote_timer = IOLoop().instance().add_timeout(
                    self.table.dismiss_time + dismiss_delay, self.vote, proto_vote)
            # 遍历所有人的投票状态
            for player in self.table.player_dict.values():
                proto_back = game_pb2.PlayerVoteResponse()
                proto_back.player = player.uuid
                if player.vote_state is not None:
                    proto_back.flag = player.vote_state
                    send(VOTE, proto_back, self.session)

        if self.table.active_seat != -1 and  self.table.state != "ShowCardState":
            # 发送出牌提醒
            self.table.clear_prompt()
            self.table.clear_actions()
            proto = game_pb2.PokerDiscardNotifyResponse()
            active_seat = self.table.active_seat

            proto.player = self.table.seat_dict[self.table.active_seat].uuid
            self.table.reset_proto(NOTIFY_DISCARD)
            self.proto.p = copy(proto)
            self.proto.send()
        #
        # elif self.table.machine.cur_state.name == 'DoubleState':
        #     # 加倍信息
        #     if len(self.table.farmer_double) >= self.table.chairs - 1:
        #         # 农民都加倍完成
        #         self.table.reset_proto(POKER_DOUBLE)
        #         proto_double_res = game_pb2.PokerDoubleResponse()
        #         for has_double_player in self.table.farmer_double:
        #             every_player = self.table.seat_dict[has_double_player]
        #             players = proto_double_res.players.add()
        #             players.seat = every_player.seat
        #             players.flag = True if every_player.seat in self.table.double_seat else False
        #         self.proto.p = copy(proto_double_res)
        #         self.proto.send()
        #     elif self.seat in self.table.farmer_double:
        #         # 农民未加倍完成给自己发
        #         self.table.reset_proto(POKER_DOUBLE)
        #         proto_double_res = game_pb2.PokerDoubleResponse()
        #         players = proto_double_res.players.add()
        #         players.seat = self.seat
        #         players.flag = True if self.seat in self.table.double_seat else False
        #         self.proto.p = copy(proto_double_res)
        #         self.proto.send()
        #     # 加倍提醒
        #     if self.seat == self.table.dealer_seat:
        #         # 地主
        #         if len(self.table.farmer_double) == self.table.chairs - 1:
        #             # 两个农民点完了
        #             proto_double_init = game_pb2.PokerDoubleInitResponse(double_list=[self.seat])
        #             send(POKER_DOUBLE_INIT, proto_double_init, self.session)
        #     else:
        #         # 农民
        #         if self.seat not in self.table.farmer_double:
        #             proto_double_init = game_pb2.PokerDoubleInitResponse()
        #             for k, v in self.table.seat_dict.iteritems():
        #                 if k != self.table.dealer_seat:
        #                     proto_double_init.double_list.append(k)
        #             send(POKER_DOUBLE_INIT, proto_double_init, self.session)
        #
        # elif self.table.machine.cur_state.name == "RobState":
        #     # 普通叫地主
        #     if self.table.conf.play_type == 1:
        #         # if self.seat == self.table.rob_seat:
        #         #     if len(self.table.rob_seat) == 0:
        #         #         # 第一个叫地主的人
        #         #         # 全发
        #         #         proto_rob_init = game_pb2.RobLandLordInitResponse()
        #         #         proto.uuid = self.table.seat_dict[self.table.rob_seat].uuid
        #         #         proto.play_type = self.table.conf.play_type
        #         #         send(ROB_DEALER_INIT, proto_rob_init, self.session)
        #         #     else:
        #         #         pass
        #         if len(self.table.rob_players) == 0:
        #             self.table.reset_proto(ROB_DEALER)
        #             proto_rob_res = game_pb2.RobLandLordReponse()
        #             # proto.uuid = player.uuid
        #             proto_rob_res.rob_score = -1
        #             proto_rob_res.win_seat = -1
        #             proto_rob_res.rob_seat = self.table.rob_seat
        #             proto_rob_res.base_score = self.table.get_base_core(self)
        #             self.proto.p = copy(proto_rob_res)
        #             self.proto.send()
        #         else:
        #             self.table.reset_proto(ROB_DEALER)
        #             proto_rob_res = game_pb2.RobLandLordReponse()
        #             rob_p = self.table.seat_dict[self.table.rob_seat]
        #             pre_p = self.table.seat_dict[rob_p.prev_seat]
        #             proto_rob_res.uuid = pre_p.uuid
        #             proto_rob_res.rob_score = pre_p.rob_score
        #             proto_rob_res.win_seat = -1
        #             proto_rob_res.rob_seat = self.table.rob_seat
        #             proto_rob_res.base_score = self.table.get_base_core(self)
        #             self.proto.p = copy(proto_rob_res)
        #             self.proto.send()
        # 明牌状态
        if self.table.state == "ShowCardState":
            proto = game_pb2.PokerShowCardInitResponse()
            proto.seat = self.table.show_card_seat
            proto.flag = self.table.get_show_cards_flag(self.table.show_card_seat)
            send(POKER_SHOW_CARDS_INIT, proto, self.session)
        # 一打四还是叫狗腿，取消计时器之后需要在重连时候弹出按钮
        if self.table.dealer_seat == self.table.spy_chair:
            proto = game_pb2.PokerDealerChooseInitResponse()
            proto.dealer_seat = self.table.dealer_seat
            proto.flag = 1 if self.seat == self.table.dealer_seat else -1
            send(POKER_DEALER_CHOOSE_INIT, proto, self.session)

    def send_prompts(self):
        proto = game_pb2.PromptResponse()
        for k, v in self.action_dict.items():
            prompt = proto.prompt.add()
            prompt.action_id = k
            prompt.prompt = v["prompt"]
            prompt.op_card.card = v["op_card"]
            for c in v["ref_cards"]:
                ref_card = prompt.ref_card.add()
                ref_card.card = c
        send(PROMPT, proto, self.session)
        self.table.logger.info(self.action_dict)

    def exit_room(self):
        if self.table.state == 'InitState':
            if self.table.conf.is_aa():
                if self.table.cur_round <= 1:
                    if self.uuid == self.table.owner:
                        # AA房主离开直接解散房间
                        self.dismiss_room()
                        return
                    else:
                        # 其他玩家返还房卡
                        self.table.request.aa_refund(self.uuid, 0)
            # 这会有一个bug
            self.table.request.exit_room(self.uuid)
            if len(self.table.seat_dict) == 1 and not self.table.conf.is_aa():
                # 非aa开房最后一个人离场直接解散
                self.table.dismiss_room()
                return
            proto = game_pb2.ExitRoomResponse()
            proto.player = self.uuid
            proto.code = 1
            for player in self.table.player_dict.values():
                send(EXIT_ROOM, proto, player.session)

            self.table.logger.info("player {0} exit room".format(self.uuid))

            self.delete()
            try:
                self.session.close()
            except Exception:
                pass
            del self.table.seat_dict[self.seat]
            del self.table.player_dict[self.uuid]
            self.table.dumps()
            self.table = None
        else:
            self.table.logger.info("player {0} exit room failed".format(self.uuid))

    def dismiss_room(self):
        # 解散房间不重复响应
        if self.table.dismiss_state:
            return
        if self.table.state == "InitState":
            # 房间未开局直接由房主解散
            if self.uuid == self.table.owner:
                self.table.dismiss_room(False)
            else:
                proto = game_pb2.DismissRoomResponse()
                proto.code = 5003
                send(DISMISS_ROOM, proto, self.session)
        else:
            # 如果是房主则直接解散
            # if self.uuid == self.table.owner:
            #     self.table.dismiss_room(False)
            #     return
            # 房间已开局则直接发起投票
            self.table.dismiss_state = True
            self.table.dismiss_sponsor = self.uuid
            self.table.dismiss_time = time.time()
            self.vote_state = True
            self.dumps()
            proto = game_pb2.SponsorVoteResponse()
            proto.room_id = self.table.room_id
            proto.sponsor = self.table.dismiss_sponsor
            proto.expire_seconds = dismiss_delay
            for player in self.table.player_dict.values():
                send(SPONSOR_VOTE, proto, player.session)
                if player.uuid == self.uuid:
                    continue
                proto_vote = game_pb2.PlayerVoteRequest()
                proto_vote.flag = True
                player.vote_timer = IOLoop().instance().add_timeout(
                    self.table.dismiss_time + dismiss_delay, player.vote, proto_vote)
            self.table.logger.info("player {0} sponsor dismiss room".format(self.uuid))

    def vote(self, proto):
        IOLoop().instance().remove_timeout(self.vote_timer)
        self.dumps()
        self.vote_state = proto.flag
        self.table.logger.info("player {0} vote {1}".format(self.uuid, self.vote_state))

        self.vote_timer = None
        proto_back = game_pb2.PlayerVoteResponse()
        proto_back.player = self.uuid
        proto_back.flag = proto.flag
        for k, v in self.table.player_dict.items():
            send(VOTE, proto_back, v.session)

        if proto.flag:
            for player in self.table.player_dict.values():
                if not player.vote_state:
                    return
            self.table.dismiss_room()
        else:
            # 只要有一人拒绝则不能解散房间1
            self.table.dismiss_state = False
            self.table.dismiss_sponsor = None
            self.table.dismiss_time = 0
            for player in self.table.player_dict.values():
                player.vote_state = None
                if player.vote_timer:
                    IOLoop.instance().remove_timeout(player.vote_timer)
                    player.vote_timer = None

    def ready(self):
        self.machine.trigger(ReadyState())

    def is_show_card_state(self, session):
        if self.state != 'ShowCardState':
            proto = game_pb2.ShowCardResponse()
            proto.code = 2
            proto.player = self.uuid
            send(SHOWCARD, proto, session)
            return False
        return True

    def get_multiple_double(self):
        """ 翻倍
        """
        double = 1
        # 地主
        if self.seat == self.table.dealer_seat:
            for i in self.table.player_dict.values():
                double = double * i.double
            return double
        # 农民
        if self.double > 1:
            dealer = self.table.seat_dict[self.table.dealer_seat]
            double = self.double * dealer.double
        return double

    def calculate_multiple(self):
        # 底分 * 抢地主叫分 * 炸弹 * 明牌 * 翻倍 * 春天/反春

        multiple_boom = self.table.get_multiple_boom()
        multiple_show = self.table.get_multiple_show()
        multiple_double = self.get_multiple_double()
        multiple_spring = self.table.get_multiple_spring()
        multiple_before_spring = multiple_boom * multiple_double * multiple_show
        if self.table.conf.times_limit:
            if multiple_before_spring >= self.table.conf.times_limit:
                multiple_spring = 1
                multiple_before_spring = self.table.conf.times_limit
        multiple = multiple_before_spring * multiple_spring
        return int(multiple)


