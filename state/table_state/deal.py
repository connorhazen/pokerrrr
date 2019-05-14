# coding: utf-8
import random
from copy import copy

from algorithm.config import init_landlords
from protocol import game_pb2
from protocol.commands import POKER_DEAL
from state.player_state.deal import DealState as PlayerDealState
from state.table_state.base import TableStateBase


class DealState(TableStateBase):
    def __init__(self):
        super(DealState, self).__init__()

    def enter(self, owner):
        super(DealState, self).enter(owner)
        owner.active_seat = -1
        # 随机地主
        owner.dealer_seat = random.randint(0, owner.chairs-1)
        cards_rest = init_landlords()
        cheat = False
        if cheat:
            owner.dealer_seat = 2
            # dealer = owner.dealer_seat = 0
            name = "poker:lemon:card:cheat:{0}"
            tile_list = []
            seat = 0
            # while seat < owner.chairs:
            #     tile = []
            #     rounds = 0
            #     cards_rest.remove("8G")
            #     cards_rest.insert(0,"8G")
            #     while rounds < 31:
            #         tile.append(cards_rest.pop())
            #         rounds += 1
            #     tile_list.append(tile)
            #     seat += 1
            tile_list.append(
                ['2H', '2S',  '3H', '3S', '3D','4H', '4S', '4D', '4C'])
            tile_list.append(
                ['6H', '6S', '7H', '7S', '7D', '8C', '8H', '8S', '9D', 'SS', 'SS'])
            tile_list.append(
                ['TH'])
            tile_list.append(
                ['TH'])
            tile_list.append(
                ['TH'])


            # tile_list.append(['TH', 'TS', 'TD', 'TC', 'JH', 'JS', 'JD', 'JC','QH', 'QS', 'QD', 'QC','KH', 'KS', 'KD', 'KC', 'AD'])
            # tile_list.append(['2H', '3H', '4H', '5H', '6H', '7H', '8H', '9H','TH', 'JH', 'QH', 'KH','AH', '2C', '3C', '4C', '5C'])
            # tile_list.append(['2S', '3S', '4S', '5S', '6S', '7S', '8S', '9S','TS', 'JS', 'QS', 'KS','AS', '6C', '7C', '8C', '9C'])
            # tile_list.append(['2D', '3D', '4D', '5D', '6D', '7D', '8D', '9D','TD', 'JD', 'QD', 'KD','AD', 'TC', 'JC', 'QC', 'KC'])

            for tmpList in tile_list:
                # print tmpList
                for card in tmpList:
                    if card in cards_rest:
                        cards_rest.remove(card)
            # while seat < owner.chairs:
            #     tile_list.append([int(i) for i in redis.lrange(name.format(seat), 0, -1)])
            #     seat += 1
            #     #print tile_list
            # cards_rest = [int(i) for i in redis.lrange(name.format("rest"), 0, -1)]
            # print cards_rest
        else:
            tile_list = []
            seat = 0
            while seat < owner.chairs:
                tile = []
                rounds = 0
                while rounds < 31:
                    tile.append(cards_rest.pop())
                    rounds += 1
                tile_list.append(tile)
                seat += 1

        # owner.cards_on_desk = cards_rest

        # owner.dealer_seat = 0
        # 预先定义狗腿牌
        owner.spy_card = '8G'
        owner.replay = {
            "room_id": owner.room_id,
            "spy_card": "8G",
            "round": owner.cur_round,
            "conf": owner.conf.settings,
            "cards_on_desk": owner.cards_on_desk,
            "game_type": 10,
            "dealer": owner.dealer_seat,
            "user": {},
            "deal": {},
            "procedure": [],
        }
        log = {}

        owner.reset_proto(POKER_DEAL)
        # owner.spy_chair = owner.dealer_seat
        for k, v in enumerate(tile_list):

            player = owner.seat_dict[k]
            player.cards_in_hand = sorted(v)
            # 给地主加牌
            if player.seat == owner.dealer_seat:
                for c2 in cards_rest:
                    player.cards_in_hand.append(c2)
                player.cards_in_hand.sort()

            if '8G' in player.cards_in_hand:
                if owner.spy_chair == -1:
                    owner.spy_chair = player.seat
                else:
                    owner.logger.fatal("spy count != 1")

            log[str(k)] = player.cards_in_hand
            # print 'player:',player.uuid,', cards:', player.cards_in_hand
            proto = game_pb2.PokerDealResponse()
            proto.dealer_seat = owner.dealer_seat
            for c in player.cards_in_hand:
                card = proto.cards_in_hand.add()
                card.card = c
            # for c2 in cards_rest:
            #     card = proto.cards_rest.add()
            #     card.card = c2
            player.proto.p = copy(proto)
            owner.replay["user"][k] = (player.uuid, player.info)
            owner.replay["deal"][k] = copy(player.cards_in_hand)
            player.machine.trigger(PlayerDealState())

        # log["cards_rest"] = cards_rest
        owner.logger.info(log)
        owner.dumps()

    # def next_state(self, owner):
    #     owner.machine.trigger(StepState())

    def execute(self, owner, event):
        super(DealState, self).execute(owner, event)
        from logic.table_action import skip_choose
        if event == "skip_choose":
            skip_choose(owner)
