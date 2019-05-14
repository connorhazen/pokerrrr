# coding: utf-8
import json
from datetime import datetime
from state.player_state.settle import SettleState
from state.table_state.base import TableStateBase
from state.table_state.restart import RestartState
from rules.table_rules.manager import TableRulesManager
from rules.define import *
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send


class SettleForRoundState(TableStateBase):
    def enter(self, owner):
        super(SettleForRoundState, self).enter(owner)
        # print "SettleForRound"
        # 将所有玩家至于结算状态
        for player in owner.player_dict.values():
            player.machine.trigger(SettleState())

        win_seat = owner.active_seat
        # 计算手牌剩余喜钱
        owner.calculate_reward_in_hand()
        # 算基础分和总分
        owner.calculate_score(win_seat)
        # 庄家阵营赢:
        if win_seat in owner.land_lord_chairs:
            # 浅拷贝
            win_player_seat_dict = owner.land_lord_chairs[:]
        else:
            win_player_seat_dict = owner.farmer_chairs[:]

        # 广播小结算数据
        log = {"uuid": owner.room_uuid, "current_round": owner.cur_round, "replay": owner.replay,
               "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "win_type": owner.win_type, "player_data": []}
        # 返回
        proto = game_pb2.PokerSettleForRoundResponse()
        proto.reward_info = json.dumps(owner.reward_info)
        # print(owner.reward_info)
        # print json.dumps(owner.reward_info)
        proto.show_multiple = owner.get_multiple_show()
        for seat in sorted(owner.seat_dict.keys()):
            i = owner.seat_dict[seat]
            # 本局得分
            p = proto.player_data.add()
            p.player = i.seat
            p.score = i.score
            p.total = i.total
            p.reward = i.reward_points
            p.show_card = i.show_card
            if i.seat in win_player_seat_dict:
                p.result = 1
            else:
                p.result = 0
            if i.seat == owner.dealer_seat:
                # 地主
                p.role = 1
            elif i.seat == owner.spy_chair:
                # 狗腿
                p.role = 2
            else:
                p.role = 0
            for c in i.cards_in_hand:
                cards = p.rest_cards.add()
                cards.card = c
            # p.times = i.calculate_multiple()
            log["player_data"].append({
                "player": i.uuid,
                "cards_in_hand": i.cards_in_hand,
                "score": i.score + i.reward_points,
                "total": i.total,
                "reward": i.reward_points,
                "result": 1 if i.seat in win_player_seat_dict else 0,
                "role": p.role,
                "show_card": p.show_card
            })

        for i in owner.player_dict.values():
            send(POKER_SETTLEMENT_FOR_ROUND, proto, i.session)
        owner.request.settle_for_round(log)

        # 构建周赛以及活动数据
        active_data = {"appId": 1, "gameId": 10, "score_data_list": []}
        for seat in sorted(owner.seat_dict.keys()):
            i = owner.seat_dict[seat]
            role = 0
            if i.seat == owner.dealer_seat:
                # 地主
                role = 1
            elif i.seat == owner.spy_chair:
                # 狗腿
                role = 2
            data_result = 1 if i.seat in win_player_seat_dict else 0
            score = 3 if data_result == 1 else 1
            if owner.spy_chair == -1 and owner.dealer_seat == seat:
                score = 5
            active_data["score_data_list"].append({
                "userId": i.uuid,
                "role": role,
                "score": score,
                "result": data_result,
                "ext": json.dumps(i.ext)
            })
        print active_data
        owner.request.sync_data(active_data)
        owner.cur_round += 1

        owner.logger.info(log)
        # 清空本局数据
        for player in owner.player_dict.values():
            player.clear_for_round()

        owner.clear_for_round()
        # 检测规则是否进入大结算
        TableRulesManager().condition(owner, TABLE_RULE_SETTLE_FOR_ROUND)

    def exit(self, owner):
        # 清空玩家的当局数据
        super(SettleForRoundState, self).exit(owner)

    def next_state(self, owner):
        owner.win_type = 0
        owner.machine.trigger(RestartState())
