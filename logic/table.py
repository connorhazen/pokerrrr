# coding: utf-8

import json
import time
from collections import Counter

from tornado.ioloop import IOLoop

from algorithm.config import MAPPING_LIST, SUITS
from logic.player import Player
from logic.session_manager import SessionMgr
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from rules.define import *
from settings import game_id, choose_delay
from settings import redis
from state.machine import Machine
from state.status import player_state_code_map
from state.table_state.ready import ReadyState
from utils.logger import Logger
from algorithm.card_type.main import get_color_count


class Table(object):
    def __init__(self, room_id, room_uuid, owner, kwargs):
        super(Table, self).__init__()
        self.room_id = room_id
        self.room_uuid = room_uuid
        self.owner = owner
        self.owner_info = None
        self.kwargs = str(kwargs)
        self.chairs = 5
        self.player_dict = {}
        self.seat_dict = {}
        self.machine = None
        self.state = None

        self.et = None
        self.dismiss_state = False
        self.dismiss_sponsor = None
        self.dismiss_time = 0
        self.logger = Logger(room_id)
        self.request = None
        self.dealer_seat = -1  # 庄家(地主)
        self.active_seat = -1  # 当前出牌玩家
        # self.active_card = 0

        self.discard_seat = -1
        self.event = None
        self.cards_total = 0
        self.win_seat_prompt = []
        self.win_seat_action = []

        self.player_prompts = []
        self.player_actions = []
        self.conf = None
        self.step = 0

        self.dice_1 = 0
        self.dice_2 = 0

        self.win_type = 0  # 1-春天 2-反春天
        self.cur_round = 1
        self.replay = {}

        self.rob_seat = -1  # 当前抢地主座位号
        self.rob_score = 0  # 抢地主 当前叫分
        self.rob_players = {}  # 抢地主

        self.rob_players_happy = []  # 欢乐抢地主

        self.last_oper_seat = -1
        self.st = time.time()
        self.cards_on_desk = []  # 桌面剩余3张牌
        self.active_card = []  # 当前打出的牌组列表
        self.active_card_type = ''  # 当前打出牌组类型

        self.boom_num = 0  # 当前炸弹总数

        self.show_card_log = {}  # 明牌记录
        self.show_card_num = 0
        self.max_show_multiple = 1  # 本局最大明牌倍数

        self.farmer_double = []  # 农民翻倍记录
        # 地主阵营
        self.land_lord_chairs = []
        # 农民阵营
        self.farmer_chairs = []
        # 叫狗腿开始时间
        self.choose_begin_time = 0
        # 临时添加计时器(控制地主选择叫狗腿4s,明牌4s,出牌16s)
        self.temp_timer = None
        # 当前正在选择明牌玩家座位号
        self.show_card_seat = -1
        # 选择明牌玩家开始时间
        self.show_card_begin_time = 0

        self.double_seat = []

        self.last_discard_seat = -1

        self.dismiss_flag = 1
        # 狗腿的座位号，选择一打四为-1
        self.spy_chair = -1
        # 狗腿牌
        self.spy_card = '8G'
        # 狗腿暴露
        self.baolu = False
        # 喜钱info
        self.reward_info = {}
        # 暂停状态，用于服务器重启或者五个玩家全部掉线之后的定时器启动判断
        self.pasue_state = False
        self.logger.info("room created")
        Machine(self)

    def dumps(self):
        data = {}
        for key, value in self.__dict__.items():
            if key in ("logger", "conf", "request"):
                continue
            elif key == "player_dict":
                data[key] = value.keys()
            elif key == "temp_timer":
                data[key] = []
            elif key == "seat_dict":
                data[key] = {k: v.uuid for k, v in value.items()}
            elif key == "reward_info":
                data[key] = {k: v for k, v in value.items()}
            elif key == "machine":
                data[key] = [None, None]
                if value.cur_state:
                    data[key][1] = value.cur_state.name
                if value.last_state:
                    data[key][0] = value.last_state.name
            else:
                data[key] = value
                # print "table dumps", data
        redis.set("table:{0}".format(self.room_id), json.dumps(data))

    def delete(self):
        self.player_dict = {}
        self.seat_dict = {}
        redis.delete("table:{0}".format(self.room_id))

    def clear_for_round(self):
        """ 清理本局数据
        """
        self.replay = {}
        self.win_seat_prompt = []
        self.win_seat_action = []
        self.last_oper_seat = -1
        self.win_type = 0
        # 扑克
        self.rob_players_happy = []
        self.active_card = []
        self.active_card_type = ''
        self.active_card_seat = -1
        # 不重置抢地主玩家直接取下一位
        # self.rob_seat = -1     # 当前抢地主座位号
        self.rob_score = 0  # 抢地主 最高分
        self.rob_players = {}  # 抢地主列表 

        self.active_seat = -1
        self.discard_seat = -1
        self.dealer_seat = -1  # 地主初始化
        self.boom_num = 0
        self.show_card_log = {}
        self.show_card_num = 0
        self.max_show_multiple = 1
        self.farmer_double = []
        self.step = 0

        self.temp_timer = None
        self.last_discard_seat = -1
        self.double_seat = []
        self.spy_chair = -1
        self.show_card_seat = -1
        self.land_lord_chairs = []
        self.farmer_chairs = []
        self.spy_card = "8G"
        self.baolu = False
        self.reward_info = {}

        self.dumps()

    def enter_room(self, player_id, info, session):
        # print 'table enter_room ', player_id, info
        if not self.owner_info and player_id == self.owner:
            self.owner_info = info
        proto = game_pb2.EnterRoomResponse()
        proto.room_id = self.room_id
        proto.owner = self.owner
        proto.game_type = game_id

        if len(self.player_dict.keys()) >= self.chairs:
            proto.code = 5002
            send(ENTER_ROOM, proto, session)
            if self.conf.is_aa():
                self.request.aa_refund(player_id, 0)
            self.logger.warn("room {0} is full, player {1} enter failed".format(self.room_id, player_id))
            return
        # 这启动一次
        if self.pasue_state:
            self.start_timer()
        player = Player(player_id, info, session, self)
        from state.player_state.init import InitState
        player.machine.trigger(InitState())
        seat = -1
        for seat in range(self.chairs):
            if seat in self.seat_dict.keys():
                continue
            break
        self.player_dict[player_id] = player
        self.seat_dict[seat] = player
        player.seat = seat
        proto.code = 1
        proto.kwargs = self.kwargs
        proto.rest_cards = self.cards_total
        for k, v in self.seat_dict.items():
            p = proto.player.add()
            p.seat = k
            p.player = v.uuid
            p.info = v.info
            p.status = player_state_code_map[v.state]
            p.is_online = 1 if v.is_online else 0
            p.total_score = v.total
        SessionMgr().register(player, session)

        send(ENTER_ROOM, proto, session)
        # print 'player cnt:', len(self.player_dict.keys())
        proto = game_pb2.EnterRoomOtherResponse()
        proto.code = 1
        proto.player = player_id
        player = self.player_dict[player_id]
        proto.info = player.info
        proto.seat = player.seat

        for i in self.player_dict.values():
            if i.uuid == player_id:
                continue
            send(ENTER_ROOM_OTHER, proto, i.session)
        player.dumps()
        self.dumps()
        self.request.enter_room(player_id)
        self.logger.info("player {0} enter room".format(player_id))
        if self.conf.is_aa():
            self.request.aa_cons(player_id)

    def dismiss_room(self, vote=True):

        # 如果是投票解散房间则进入大结算，否则直接推送房主解散命令

        def _dismiss():
            # 弹出大结算
            from state.table_state.settle_for_room import SettleForRoomState
            self.machine.trigger(SettleForRoomState())
            self.request.load_minus()

        if vote and self.state != "InitState":
            # 房间内游戏中投票解散
            _dismiss()

        else:
            # 0-没开始解散 1-投票 2-外部解散或者游戏进行中房主解散
            vote_flag = 2
            if vote:
                # 房间内投票
                vote_flag = 1
            else:
                if self.state == "InitState":
                    # 房主在游戏未开始时解散
                    vote_flag = 0
            if vote_flag == 2:
                # 到这说明游戏在进行中房主解散
                # 在游戏内部已经做了限制不会走到这里
                # 在游戏外部如果游戏进行中不让解散
                # 这里直接返回吧
                # self.dismiss_flag = 2
                # _dismiss()
                return
            else:

                # 游戏未开始时和游戏外房主解散直接返回0,2。
                # 0代表外开始时解散，2代表外部解散或者游戏进行中房主解散
                # 直接返回一个flag就完事了
                proto = game_pb2.DismissRoomResponse()
                proto.code = 1
                proto.flag = vote_flag
                for k, v in self.player_dict.items():
                    send(DISMISS_ROOM, proto, v.session)
                # 这个位置没－1导致房间数量一直上升
                if vote_flag == 1:
                    self.request.load_minus()
        self.logger.info("room {0} dismiss".format(self.room_id))
        from logic.table_manager import TableMgr
        self.request.dismiss_room(self)
        TableMgr().dismiss(self.room_id)
        for player in self.player_dict.values():
            try:
                player.session.close()
            except Exception:
                pass
            player.delete()

        self.delete()

    def is_all_ready(self):
        # print 'is_all_ready = ', self.chairs, len(self.player_dict)
        if len(self.player_dict) != self.chairs:
            return
        for player in self.player_dict.values():
            if player.state != "ReadyState":
                return
        if self.cur_round == 1:
            self.request.load_plus()
        self.machine.trigger(ReadyState())



    def is_all_players_do_action(self):
        self.dumps()
        self.logger.debug(("during player do actions", "prompts", self.player_prompts, "actions", self.player_actions))
        if len(self.player_actions) != len(self.player_prompts):
            return
        self.logger.debug(("after player do actions", "prompts", self.player_prompts, "actions", self.player_actions))
        # 没有提示
        if not self.player_prompts:
            self.seat_dict[self.active_seat].machine.next_state()
        # self.clear_prompt()
        self.logger.debug(("after player do actions1", "prompts", self.player_prompts, "actions", self.player_actions))
        max_weight, max_weight_player = self.get_highest_weight_action_player()
        # 有提示但是都选择过
        if not max_weight:
            self.seat_dict[self.active_seat].machine.next_state()
            return
        self.logger.debug(("after player do actions3", "prompts", self.player_prompts, "actions", self.player_actions))
        target = -1
        if max_weight in (PLAYER_ACTION_TYPE_WIN_DRAW, PLAYER_ACTION_TYPE_WIN_DISCARD):
            if max_weight == PLAYER_ACTION_TYPE_WIN_DRAW:
                assert len(max_weight_player) == 1
                self.win_type = TABLE_WIN_TYPE_DISCARD_DRAW
            else:
                self.seat_dict[self.last_oper_seat].pao_cnt += 1
                target = self.win_seat_action[0]
                loser = self.last_oper_seat
                if len(self.win_seat_action) > 1:
                    for i in self.win_seat_action:
                        t = (loser - i + self.conf.chairs) % self.conf.chairs
                        print 't = ', t
                        r = (loser - target + self.conf.chairs) % self.conf.chairs
                        print 'r = ', r
                        if t > r:
                            target = i
                self.win_type = TABLE_WIN_TYPE_DISCARD_ONE
                # self.dealer_seat = target
                # self.win_seat_action[0] = target
        else:
            self.clear_prompt()

        from rules.rules_map import rules_dict
        hupai = 0
        for player in max_weight_player:
            rule = rules_dict[player.action_rule]
            if player.action_rule in ("DiscardWinRule", "QGWinRule"):
                # if self.win_seat_action[0] == player.seat:
                if target != -1 and target == player.seat:
                    self.logger.debug(
                        ("after player do actions4", "prompts", self.player_prompts, "actions", self.player_actions))
                    self.replay["procedure"].append(
                        [{"action": {"rule": player.action_rule, "op_card": player.action_op_card,
                                     "ref_cards": player.action_ref_cards,
                                     "prompt": player.action_weight},
                          "seat": player.seat}])
                    hupai = 1
                    rule.action(player)
            else:
                self.logger.debug(
                    ("after player do actions5", "prompts", self.player_prompts, "actions", self.player_actions))
                self.replay["procedure"].append(
                    [{"action": {"rule": player.action_rule, "op_card": player.action_op_card,
                                 "ref_cards": player.action_ref_cards,
                                 "prompt": player.action_weight},
                      "seat": player.seat}])
                hupai = 1
                rule.action(player)

            self.logger.debug(("procedure", "prompts", self.player_prompts, "actions", self.player_actions, "rules",
                               player.action_rule))

            if player.action_rule in ['DiscardWinRule', 'DrawWinRule'] and not hupai:
                return
        # self.clear_prompt()
        self.clear_actions()
        # self.win_seat_prompt = []
        # self.win_seat_action = []
        self.logger.debug(("after player do actions2", "prompts", self.player_prompts, "actions", self.player_actions))
        # 如果有人胡牌
        if max_weight in (PLAYER_ACTION_TYPE_WIN_DRAW, PLAYER_ACTION_TYPE_WIN_DISCARD):
            self.clear_prompt()
            from state.table_state.end import EndState
            self.machine.trigger(EndState())

    def clear_prompt(self):
        self.player_prompts = []
        for player in self.player_dict.values():
            player.del_prompt()

    def clear_actions(self):
        self.player_actions = []
        self.logger.debug("clear actions")
        for player in self.player_dict.values():
            player.del_action()

    def get_highest_weight_action_player(self):
        self.logger.debug(("get_highest_weight_action_player ", self.player_actions))
        max_weight = 0
        for player_id in self.player_actions:
            player = self.player_dict[player_id]
            weight = player.action_weight
            if weight > max_weight:
                max_weight = weight
        max_weight_player = []
        for player_id in self.player_actions:
            player = self.player_dict[player_id]
            if player.action_weight == max_weight:
                max_weight_player.append(player)
            # else:
            # player.machine.next_state()

        return max_weight, max_weight_player

    def reset_proto(self, cmd):
        for player in self.player_dict.values():
            player.proto.require()
            player.proto.c = cmd

    def rob_all_cancel(self):
        # 全都不抢不换初始抢分人
        # self.rob_seat = self.seat_dict[self.rob_seat].prev_seat
        self.rob_score = 0
        self.rob_players = {}
        self.rob_players_happy = []

        for player in self.player_dict.values():
            player.rob_score = -1

    def check_spring(self, player):
        """ 判断春天/反春天
        """
        if player.seat == self.dealer_seat:
            # 春天
            num = 0
            for i in self.player_dict.values():
                if i.uuid == player.uuid:
                    continue
                if i.cards_discard:
                    break
                num += 1
            if num >= (self.chairs - 1):
                self.win_type = 1
        else:
            # 反春天
            dealer = self.seat_dict[self.dealer_seat]
            if len(dealer.cards_discard) == 1:
                self.win_type = 2

    def get_rob_score(self):
        """ 抢地主叫分
        """
        if self.conf.play_type == 1:
            # 经典斗地主
            return self.rob_score
        elif self.conf.play_type == 2:
            # 欢乐斗地主
            return reduce(lambda x, y: x * y, [item[1] for item in self.rob_players_happy if item[1]])

    def get_multiple_boom(self):
        """ 炸弹倍数 
        """
        # 炸弹算分个数上限
        if self.conf.max_bomb:
            if self.boom_num > self.conf.max_bomb:
                self.boom_num = self.conf.max_bomb
        return (2 ** self.boom_num)

    def get_multiple_show(self):
        """ 明牌倍数
        """
        return self.max_show_multiple

    def get_multiple_spring(self):
        """ 春天/反春天 翻倍
        """
        if self.win_type > 0:
            return 2
        return 1

    def calculate_score_deal(self, player):
        # 底分 * 抢地主叫分 * 炸弹 * 明牌 * 翻倍 * 春天/反春 
        base_score = self.conf.base_score
        rob_score = self.get_rob_score()
        multiple_boom = self.get_multiple_boom()
        multiple_show = self.get_multiple_show()
        multiple_double = player.get_multiple_double()
        multiple_spring = self.get_multiple_spring()

        score = base_score * rob_score * multiple_boom * multiple_show * multiple_double * multiple_spring

        return int(score)

    def exchange(self, cards):
        # 牌提取成数组
        return [MAPPING_LIST.index(r) for r, s in cards]

    # 计算手牌里的剩余喜钱
    def calculate_reward_in_hand(self):
        if self.state != "SettleForRoundState":
            return
        if not self.conf.reward_type:
            return
        # 得分 = 5 * 自己得分 - 总得分
        total_points = 0
        # 计算所有自己得分和总得分
        for player in self.player_dict.values():
            if len(player.cards_in_hand) >= 3:
                player.temp_reward_point = 0
                jack_cards = []
                bomb_cards_dict = {}  # {card_value, card_list}
                cards = self.exchange(player.cards_in_hand)
                lis = Counter(cards)
                for r, num in lis.most_common():
                    if num >= 5:
                        bomb_cards_dict[r] = []
                for card in player.cards_in_hand:
                    card_value = MAPPING_LIST.index(card[0])
                    if card in ['BB', 'SS']:
                        jack_cards.append(card)
                    elif card_value in bomb_cards_dict.keys():
                        bomb_cards_dict[card_value].append(card)
                for bomb_card_value in bomb_cards_dict.keys():
                    point = self.get_reward_points(bomb_cards_dict[bomb_card_value], "bomb")
                    if point > 0:
                        player.temp_reward_point += point
                        total_points += point
                        if player.seat not in self.reward_info.keys():
                            self.reward_info[player.seat] = []
                        self.reward_info[player.seat].append([bomb_cards_dict[bomb_card_value], point])
                if len(jack_cards) == 3 and len(list(set(jack_cards))) == 1:
                    point = 1*self.conf.base_score
                    player.temp_reward_point += point
                    total_points += point
                    if player.seat not in self.reward_info.keys():
                        self.reward_info[player.seat] = []
                    self.reward_info[player.seat].append([jack_cards, point])
                elif len(jack_cards) > 3:
                    point = self.get_reward_points(jack_cards, "jackBomb")
                    player.temp_reward_point += point
                    total_points += point
                    if player.seat not in self.reward_info.keys():
                        self.reward_info[player.seat] = []
                    self.reward_info[player.seat].append([jack_cards, point])
        if total_points > 0:
            # 给每人分配分数
            for player in self.player_dict.values():
                player.reward_points += 5 * player.temp_reward_point - total_points

    def calculate_score(self, winner):
        # 算基础分
        base_score = self.conf.base_score
        # 一打四当成加倍来算，2018.4.16换成4倍之前是2倍，之前2倍是因为地主阵营少一个人，现在4倍是在之前基础上再翻一倍，2018.5.3地主输又改回去了
        # 一打四
        multiple_single = 1
        if self.spy_chair == -1:
            # 地主赢4倍
            if winner == self.dealer_seat:
                multiple_single = 4
            # 地主输2倍
            else:
                multiple_single = 2

        # multiple_single = 4 if self.spy_chair == -1 else 1
        # 明牌倍数
        show = self.get_multiple_show()
        multiple_total = show * multiple_single
        # print base_score, multiple_single, show, multiple_total
        if winner in self.land_lord_chairs:
            win_seats = self.land_lord_chairs[:]
            lose_seats = self.farmer_chairs[:]
        else:
            win_seats = self.farmer_chairs[:]
            lose_seats = self.land_lord_chairs[:]
        for win_seat in win_seats:
            win_player = self.seat_dict[win_seat]
            for lose_seat in lose_seats:
                lose_player = self.seat_dict[lose_seat]
                lose_player.score -= (base_score * multiple_total)
                win_player.score += (base_score * multiple_total)
        # 算总得分
        for player in self.seat_dict.values():
            player.base_total += player.score
            player.total += player.score + player.reward_points
            player.reward_total += player.reward_points

    def get_base_core(self, player):
        base_score = self.conf.base_score
        rob_score = self.get_rob_score()
        if rob_score == 0:
            # 没到叫分环节
            rob_score = 1
        score = base_score * rob_score
        return score

    def get_multiple(self, player):
        if player.seat == self.dealer_seat:
            dealer_score = 0
            for farmer in self.seat_dict.values():
                if farmer.seat == player.seat:
                    continue
                dealer_score += self.do_get_multiple(farmer)
            return int(dealer_score)
        else:
            score = self.do_get_multiple(player)
            return score

    def do_get_multiple(self, player):
        multiple_boom = self.get_multiple_boom()
        multiple_show = self.get_multiple_show()
        multiple_double = player.get_multiple_double()
        score = multiple_boom * multiple_show * multiple_double
        multiple_spring = self.get_multiple_spring()
        multiple_before_spring = multiple_boom * multiple_double * multiple_show
        if self.conf.times_limit:
            if multiple_before_spring >= self.conf.times_limit:
                multiple_spring = 1
                multiple_before_spring = self.conf.times_limit
        multiple = multiple_before_spring * multiple_spring

        return int(multiple)

    def change_spy_card(self):
        dealer = self.seat_dict[self.dealer_seat]
        # 浅拷贝手牌
        cards = dealer.cards_in_hand[:]
        from collections import Counter
        lis = Counter(cards)
        pre_cards = []
        for r, num in lis.most_common():
            # 将数量为2的牌筛选出来，不包含大小王和红桃8
            if num == 2 and r not in ['8H', 'BB', 'SS']:
                pre_cards.append(r)
        # 加一个判断以防万一找不到牌
        if not pre_cards:
            return False
        pre_cards_num = [MAPPING_LIST.index(r) for r, s in pre_cards]
        pre_cards_num.sort(reverse=True)
        max_num = pre_cards_num[0]
        sign = False
        for suit in SUITS:
            card = MAPPING_LIST[max_num] + suit
            if card in pre_cards:
                self.spy_card = card
                sign = True
                break
        return sign

    def change_spy_chair(self):
        if not self.spy_card or self.spy_card == '8G':
            self.logger.info("spy_card {0} not legal".format(self.spy_card))
            return False
        for player in self.player_dict.values():
            if player.seat == self.dealer_seat:
                continue
            if self.spy_card in player.cards_in_hand:
                self.spy_chair = player.seat
                return True

    def get_reward_points(self, cards, cards_type):
        # 普通炸弹
        sum_reward = 0
        count = len(cards)
        if cards_type == "bomb":
            # (牌数-6)+(同花色-4)
            colors = get_color_count(cards)
            count_point = 0
            color_point = 0
            if count > 6:
                count_point = count - 6
            if colors['red'] > 4:
                color_point += colors['red'] - 4
            if colors['black'] > 4:
                color_point += colors['black'] - 4
            sum_reward = count_point + color_point
        # 王炸
        elif cards_type == "jackBomb":
            if count == 3:
                sum_reward = 1
            elif count == 4:
                sum_reward = 2
            elif count == 5:
                sum_reward = 4
            elif count == 6:
                sum_reward = 6
        return sum_reward * self.conf.base_score

    def calculate_reward_points(self):
        # 配置文件不带喜
        if not self.conf.reward_type:
            return
        # 得分出问题
        points = self.get_reward_points(self.active_card, self.active_card_type)
        if points <= 0:
            return
        plus_player = self.seat_dict[self.active_seat]
        plus_player.reward_counts += points/self.conf.base_score
        for player in self.player_dict.values():
            if player.seat == self.active_seat:
                continue
            player.reward_points -= points
            plus_player.reward_points += points

        for e_player in self.player_dict.values():
            reward_proto = game_pb2.PokerRewardPointsResponse()
            reward_proto.plus_points = 4 * points
            reward_proto.reduce_points = points
            reward_proto.seat = self.active_seat
            send(POKER_REWARD, reward_proto, e_player.session)
        if self.active_seat not in self.reward_info.keys():
            self.reward_info[self.active_seat] = []
        self.reward_info[self.active_seat].append([self.active_card, points])
        self.replay["procedure"].append({"reward": [plus_player.uuid, 4 * points]})

    def get_show_cards_flag(self, seat):
        if seat in self.land_lord_chairs:
            # 地主阵营
            for lord in self.land_lord_chairs:
                if self.seat_dict[lord].show_card == 1:
                    return -1
            return 1
        else:
            # 农民阵营
            for farmer in self.farmer_chairs:
                if self.seat_dict[farmer].show_card == 1:
                    return -1
            return 1

    def init_camp(self):
        self.land_lord_chairs.append(self.dealer_seat)
        if self.spy_chair != self.dealer_seat:
            self.land_lord_chairs.append(self.spy_chair)
        for i in range(self.chairs):
            if i not in self.land_lord_chairs:
                self.farmer_chairs.append(i)

    def notify_goutui(self):
        self.baolu = True
        proto = game_pb2.PokerExposeResponse()
        proto.seat = self.spy_chair
        self.replay["procedure"].append({"notify_goutui": self.spy_chair})
        for player in self.player_dict.values():
            send(POKER_EXPOSE, proto, player.session)

    def pasue_table_timer(self):
        if self.temp_timer:
            IOLoop().instance().remove_timeout(self.temp_timer)
            self.temp_timer = None

    def start_timer(self):
        # 直接重新进入当前状态即可激活计时器,bug:pasue_state没清，只要进来就先清除
        self.pasue_state = False
        if self.temp_timer:
            self.logger.fatal("table start_timer but the temp_time exist table_state:{0}".format(self.state))
            return
        # if self.state in ["DealerChooseState", "ShowCardState"]:
        #     self.machine.trigger(self.machine.cur_state)




    def broadcast_all(self, message):
        """ 系统广播
        """
        proto = game_pb2.CommonNotify()
        proto.messageId = 4
        proto.sdata = message

        for player in self.player_dict.values():
            send(NOTIFY_MSG, proto, player.session)
