# coding: utf-8

from copy import copy

from algorithm.base import compare
from algorithm.card_type.main import match_type
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from rules.define import *
from settings import game_id
from state.player_state.pause import PauseState


def discard(player, proto):
    from state.player_state.wait import WaitState

    if player.seat != player.table.active_seat:
        return
    type = proto.type
    cards = []
    for i in proto.cards:
        cards.append(i.card)
    # print set(cards)
    if set(cards) - set(player.cards_in_hand):
        # 出不存在的牌的时候同步手牌
        proto = game_pb2.PokerSynchroniseCardsResponse()
        for i in player.cards_in_hand:
            c = proto.card.add()
            c.card = i
        send(POKER_SYNCHRONISE_CARDS, proto, player.session)
        player.table.logger.warn("player {0} discard {1} not exist in hand".format(player.seat, cards))
        return
    # 强制地主出牌如果走到这说明作弊了

    if player.table.step == 0 and not cards:
        proto = game_pb2.PokerDiscardResponse()
        proto.player = player.uuid
        proto.code = -2
        proto.rest_cards_count = len(player.cards_in_hand)
        player.table.reset_proto(POKER_DISCARD)
        player.proto.p = copy(proto)
        player.proto.send()
        player.table.logger.warn("player {0} is landlord and does not discard".format(player.seat, cards))
        return

    if player.state == "PromptState":
        player.del_prompt()
        player.table.clear_prompt()
        player.machine.next_state()
        player.table.logger.fatal("{0} client send discard event without pass".format(player.uuid))

    proto = game_pb2.PokerDiscardResponse()
    proto.player = player.uuid
    proto.code = 2
    if cards and type == 1:
        card_type = match_type(cards, game_id)
        if card_type:
            proto.card_type = card_type
            # 其余两家要不起之后可以出任意牌
            if player.table.last_discard_seat == player.seat:
                rcode = 1
            else:
                rcode = compare(player, cards, card_type=card_type)
            if rcode != 1:
                proto.code = rcode
                # proto.rest_cards_count = len(player.cards_in_hand) - len(cards)
                proto.rest_cards_count = len(player.cards_in_hand)
                player.table.reset_proto(POKER_DISCARD)
                player.proto.p = copy(proto)
                player.proto.send()
                return
        else:
            proto.code = -2
            proto.rest_cards_count = len(player.cards_in_hand)
            player.table.reset_proto(POKER_DISCARD)
            player.proto.p = copy(proto)
            player.proto.send()
            return

        player.table.last_discard_seat = player.seat
        player.table.active_card = cards
        player.table.active_seat = player.seat
        player.table.active_card_type = card_type
        if card_type in ['bomb', 'jackBomb']:
            player.bomb_cnt += 1
            player.table.boom_num += 1
            # 喜钱
            player.table.calculate_reward_points()

        for i in cards:
            player.cards_in_hand.remove(i)
            c = proto.cards.add()
            c.card = i
        proto.rest_cards_count = len(player.cards_in_hand)

    else:
        # 过滤重复点过
        if type == 2 and player.table.last_discard_seat == player.seat:
            proto.code = -2
            proto.rest_cards_count = len(player.cards_in_hand)
            player.table.reset_proto(POKER_DISCARD)
            player.proto.p = copy(proto)
            player.proto.send()
            return
        # 出牌列表为空
        if type == 1 and not cards:
            proto.code = -2
            proto.rest_cards_count = len(player.cards_in_hand)
            player.table.reset_proto(POKER_DISCARD)
            player.proto.p = copy(proto)
            player.proto.send()
            return

    player.table.replay["procedure"].append({"discard": [player.uuid, cards]})
    player.table.logger.info("player {0} discard {1}".format(player.seat, cards))
    if player.table.spy_card in cards and player.seat != player.table.dealer_seat and not player.table.baolu:
        player.table.notify_goutui()
    # player.table.last_oper_seat = player.seat
    player.table.discard_seat = player.seat
    player.last_cards_discard = cards[:]
    if cards:
        player.cards_discard.append(cards)
    player.table.step += 1

    player.table.reset_proto(POKER_DISCARD)
    for i in player.table.player_dict.values():
        # if i.uuid == player.uuid:
        #     continue
        i.proto.p = copy(proto)
        if i.machine.cur_state.name == 'PromptDiscardState':
            i.machine.trigger(WaitState())

        if i.uuid != player.uuid:
            i.machine.cur_state.execute(i, "other_discard")
        i.proto.send()

    if player.table.player_prompts:
        player.machine.trigger(PauseState())
    else:
        # player.machine.next_state()
        from rules.player_rules.manager import PlayerRulesManager
        PlayerRulesManager().condition(player, PLAYER_RULE_WIN)


def other_discard(player):
    from rules.player_rules.manager import PlayerRulesManager
    PlayerRulesManager().condition(player, PLAYER_RULE_DISCARD)


def rob_skip(player):
    from rules.player_rules.manager import PlayerRulesManager
    PlayerRulesManager().condition(player, PLAYER_RULE_ROB)


def skip_wait(player):
    from rules.player_rules.manager import PlayerRulesManager
    PlayerRulesManager().condition(player, PLAYER_RULE_DOUBLE)


def rob_dealer(player, proto):
    """ 经典抢地主
    """
    rob_score = proto.rob_code
    win_seat = rob_seat = -1
    cancel = 0
    if player.table.conf.play_type != 1:
        return
        # 当前没有轮到该玩家抢地主
    if player.table.rob_seat != player.seat:
        return
    # 该玩家已经抢过了
    if player.seat in player.table.rob_players:
        return
    # 每次抢地主的分数都要比上次大 
    if rob_score and rob_score <= player.table.rob_score:
        return
    # 玩家下的分正确再存
    if rob_score:
        player.table.rob_score = rob_score
    # 用于控制抢地主结束
    player.table.rob_players[player.seat] = rob_score
    # 重连时用作记录
    if rob_score >= 0:
        player.rob_score = rob_score
    if rob_score >= 3:
        win_seat = player.seat
    else:
        if len(player.table.rob_players) >= player.table.chairs:
            dic = player.table.rob_players
            win_seat = sorted(dic, key=lambda x: dic[x])[-1]
            if player.table.rob_players[win_seat] == 0:
                win_seat = -1
                cancel = 1
        else:
            player.table.rob_seat = rob_seat = player.next_seat

    proto = game_pb2.RobLandLordReponse()
    proto.uuid = player.uuid
    proto.rob_score = rob_score
    proto.win_seat = win_seat
    proto.rob_seat = rob_seat
    proto.base_score = player.table.get_base_core(player)
    if win_seat != -1:
        for c2 in player.table.cards_on_desk:
            card = proto.cards_rest.add()
            card.card = c2
    player.table.reset_proto(ROB_DEALER)
    for i in player.table.player_dict.values():
        # player.machine.trigger(RobState())
        # 给所有人发包括自己
        # if i.uuid == player.uuid:
        #     continue
        i.proto.p = copy(proto)
        i.proto.send()
    player.table.replay["procedure"].append({"rob_dealer": [player.uuid, rob_score]})

    # 确定地主
    if win_seat != -1:
        player.table.dealer_seat = win_seat
        player.table.seat_dict[player.table.dealer_seat].land_lord_times += 1
        for card in player.table.cards_on_desk:
            # 给地主加牌
            player.table.seat_dict[win_seat].cards_in_hand.append(card)
        for i in player.table.player_dict.values():
            i.machine.cur_state.execute(i, "rob_skip")
        player.table.replay["procedure"].append({"rob_confirm": [player.seat, rob_score]})
    if cancel:
        player.table.rob_all_cancel()
        from state.table_state.deal import DealState
        player.table.machine.trigger(DealState())
    player.dumps()


def rob_dealer_happy(player, proto):
    """ 欢乐抢地主
    """
    rob_score = proto.rob_score
    win_seat = rob_seat = -1
    cancel = 0
    if player.table.conf.play_type != 2:
        return
        # 当前没有轮到该玩家抢地主
    if player.table.rob_seat != player.seat:
        return
    # 该玩家已经抢过了
    if rob_score == player.rob_score:
        return
    # 放弃的不能在抢地主
    if not player.rob_score:
        return
    # 首次不能抢地主
    if player.table.rob_score == 0 and rob_score == 2:
        return
    # 地主只能被叫一次 
    if player.table.rob_score == 1 and rob_score == 1:
        return
    # 抢地主后不能在叫
    if player.table.rob_score == 2 and rob_score == 1:
        return

    player.table.rob_score = rob_score if rob_score else 0
    player.table.rob_players_happy.append([player.seat, rob_score])
    player.rob_score = rob_score

    def get_win_seat(player, max_score):
        lis = player.table.rob_players_happy[::-1]
        result = None
        for item in lis:
            if item[1] == max_score:
                result = item[0]
                break
        return result

    max_score = max([i[0] for i in player.table.rob_players_happy])
    # 只有一个叫地主的
    if max_score == 1 and len(player.table.rob_players_happy) == player.table.chairs:
        win_seat = get_win_seat(player, max_score)
    else:
        if len(player.table.rob_players) >= player.table.chairs + 1:
            win_seat = get_win_seat(player, max_score)
        else:
            def set_next(player):
                next_player = player.table.seat_dict[player.next_seat]
                if next_player.rob_score == 0:
                    set_next(next_player)
                    return
                if next_player.table.rob_seat == next_player.seat:
                    return
                next_player.table.rob_seat = next_player.seat
                global rob_seat
                rob_seat = next_player.seat

            set_next(player)
            if player.table.rob_seat == player.seat and player.rob_score == 0:
                # 全都pass 重新发牌
                rob_seat = -1
                cancel = 1

    proto = game_pb2.RobLandLordReponse()
    proto.seat = player.seat
    proto.rob_score = rob_score
    proto.win_seat = win_seat
    proto.rob_seat = rob_seat
    if win_seat != -1:
        for c2 in player.table.cards_on_desk:
            card = proto.cards_rest.add()
            card.card = c2
    player.table.reset_proto(ROB_DEALER_HAPPY)
    for i in player.table.player_dict.values():
        # player.machine.trigger(RobState())
        if i.uuid == player.uuid:
            continue
        i.proto.p = copy(proto)
        i.proto.send()
    # 刷新面板分
    for i in player.table.player_dict.values():
        score_proto = game_pb2.PokerScoreResponse()
        score_proto.multiple = i.table.get_multiple(i)
        send(POKER_SCORE, score_proto, i.session)
    player.table.replay["procedure"].append({"rob_dealer_happy": [player.uuid, rob_score]})
    # 确定地主
    if win_seat != -1:
        player.table.dealer_seat = win_seat
        player.table.seat_dict[player.table.dealer_seat].land_lord_times += 1
        for i in player.table.player_dict.values():
            i.machine.cur_state.execute(i, "rob_skip")
        player.table.replay["procedure"].append({"rob_confirm": [player.seat, rob_score]})
    if cancel:
        player.table.rob_all_cancel()
        from state.table_state.deal import DealState
        player.table.machine.trigger(DealState())
    player.dumps()


def double(player, proto):
    """ 是否要翻倍
    """
    double = proto.double
    if double not in [1, 2]:
        return
    # 地主要在农民翻倍后 才可以翻倍
    has_dealer = False
    if player.seat == player.table.dealer_seat:
        # 防作弊所有农民都翻倍选择后才进行下去
        if len(player.table.farmer_double) < player.table.chairs - 1:
            return
        has_dealer = True
    if player.seat not in player.table.farmer_double:
        player.table.farmer_double.append(player.seat)

    player.double = double
    if double == 2:
        if player.seat not in player.table.double_seat:
            player.table.double_seat.append(player.seat)
        if has_dealer:
            # 刷新倍数
            for i in player.table.player_dict.values():
                score_proto = game_pb2.PokerScoreResponse()
                score_proto.multiple = i.table.get_multiple(i)
                send(POKER_SCORE, score_proto, i.session)

    if len(player.table.farmer_double) >= player.table.chairs - 1:
        # 所有人刷新一遍倍数
        for i in player.table.player_dict.values():
            score_proto = game_pb2.PokerScoreResponse()
            score_proto.multiple = i.table.get_multiple(i)
            send(POKER_SCORE, score_proto, i.session)

    proto = game_pb2.PokerDoubleResponse()

    player.table.reset_proto(POKER_DOUBLE)

    if has_dealer:
        # 地主加倍通知
        for every_player in player.table.player_dict.values():
            players = proto.players.add()
            players.seat = every_player.seat
            players.flag = True if every_player.seat in player.table.double_seat else False
        for i in player.table.player_dict.values():
            i.proto.p = copy(proto)
            i.proto.send()

    else:
        if len(player.table.farmer_double) < player.table.chairs - 1:
            # 农民1给自己发:
            # if i.seat == player.seat or  i.seat == player.table.dealer_seat:
            # for i in player.table.player_dict.values():
            #     if i.seat == player.seat:
            players = proto.players.add()
            players.seat = player.seat
            players.flag = True if player.seat in player.table.double_seat else False
            player.proto.p = copy(proto)
            player.proto.send()
            # 刷新自己的分
            score_proto = game_pb2.PokerScoreResponse()
            score_proto.multiple = player.table.get_multiple(player)
            send(POKER_SCORE, score_proto, player.session)
        else:
            # 农民2发给所有人
            for every_player in player.table.player_dict.values():
                if every_player.seat == player.table.dealer_seat:
                    continue
                players = proto.players.add()
                players.seat = every_player.seat
                players.flag = True if every_player.seat in player.table.double_seat else False
            for i in player.table.player_dict.values():
                i.proto.p = copy(proto)
                i.proto.send()

            # 没人叫地主，跳过地主加倍
            if len(player.table.double_seat) == 0:
                player.table.seat_dict[player.table.dealer_seat].machine.cur_state.execute(
                    player.table.seat_dict[player.table.dealer_seat], "skip_wait")
                player.dumps()
    if not has_dealer and len(player.table.farmer_double) >= player.table.chairs - 1 and len(
            player.table.double_seat) >= 1:
        for k, v in player.table.seat_dict.iteritems():
            proto = game_pb2.PokerDoubleInitResponse(double_list=[player.table.dealer_seat])
            send(POKER_DOUBLE_INIT, proto, v.session)
    player.table.replay["procedure"].append({"double": [player.seat, double]})
    player.machine.cur_state.execute(player, "skip_wait")
    player.dumps()


def show_card(player, proto):
    """ 明牌
    """
    if player.table.show_card_seat != player.seat or player.has_chosen_ming:
        return
    # 这个位置做个调整，取消计时器的时候会有一个问题，前台会返回2但是这个结果是-1所以这个位置不能做return判断
    # if player.table.get_show_cards_flag(player.seat) != 1:
    if player.table.get_show_cards_flag(player.seat) != 1 and proto.flag != 2:
        # 判断不能明牌和选择明牌
        return

    # 1明牌，2不明牌
    flag = proto.flag
    if flag not in [1, 2]:
        player.table.logger.fatal("show_card error flag:{0}".format(flag))
        return
    else:
        player.show_card = flag
        player.has_chosen_ming = True

    if flag == 1:
        player.table.replay["procedure"].append({"show_card": player.seat})
        player.table.max_show_multiple *= 2
    player.dumps()
    # 桌子明牌下一步，为了取消计时器临时做的一个解决方案
    player.table.machine.cur_state.execute(player.table, "player_show_step")


def show_card_dealer(player, proto):
    """ 地主二次明牌
    """
    step = proto.step
    s1, s2 = divmod(step, 10)
    if s1 and s1 != 3:
        return

    for k, v in player.table.player_dict.iteritems():
        if k == player.uuid:
            continue
        proto = game_pb2.ShowCardResponse()
        proto.code = 0
        proto.player = k
        proto.step = step
        if step != 0:
            for c in player.cards_in_hand:
                card = proto.cards.add()
                card.card = c
        send(SHOWCARD, proto, v.session)

    player.show_card = step
    multiple = player.table.conf.show_card_config['double'].get(step, 1)
    if multiple > player.table.max_show_multiple:
        player.table.max_show_multiple = multiple
    # 刷新面板分
    for i in player.table.player_dict.values():
        score_proto = game_pb2.PokerScoreResponse()
        score_proto.multiple = i.table.get_multiple(i)
        send(POKER_SCORE, score_proto, i.session)
    player.table.replay["procedure"].append({"show_card": [player.seat]})
    from rules.player_rules.manager import PlayerRulesManager
    PlayerRulesManager().condition(player, PLAYER_RULE_SHOWCARD_DEALER)
    player.dumps()


def action(player, proto):
    player.table.logger.debug(
        ("when player do action", "prompts", player.table.player_prompts, "proto.action_id", proto.action_id))
    if proto.action_id:
        # 判断是否在提示列表中
        if proto.action_id in player.action_dict.keys():
            # 判断是否在提示列表中
            player.table.logger.info("player {0} do {1} action {2}".format(
                player.seat, proto.action_id, player.action_dict[proto.action_id]))
            if player.seat in player.table.win_seat_prompt and player.seat not in player.table.win_seat_action:
                player.table.win_seat_action.append(player.seat)
            player.action(proto.action_id)

            if player.action_rule not in ['DrawWinRule',
                                          'DiscardWinRule'] and player.seat in player.table.win_seat_prompt:
                # player.table.win_seat_prompt.remove(player.seat)
                if player.seat in player.table.win_seat_action:
                    player.table.win_seat_action.remove(player.seat)
        else:
            player.table.logger.warn("player {0} do {1} not illegal".format(player.seat, proto.action_id))
            return
    else:
        player.del_prompt()
        if player.seat in player.table.win_seat_prompt and player.seat in player.table.win_seat_action:
            player.table.win_seat_action.remove(player.seat)

    if player.state == "DiscardState":
        # 玩家处于自摸点过出牌状态
        player.table.clear_prompt()
    else:
        # 玩家处于其他玩家出牌提示状态
        if player.uuid not in player.table.player_actions:
            player.table.player_actions.append(player.uuid)
        player_action_rule = player.action_rule
        # 将低优先级的玩家直接过掉
        for player_id in player.table.player_prompts:
            if player_id == player.uuid:
                continue
            p = player.table.player_dict[player_id]
            # 只有在其他玩家没做出选择才可以直接pass， 但是不能重复pass
            if p.highest_prompt_weight() < player.action_weight and p.action_id == 0 and \
                    p.uuid not in player.table.player_actions:
                player.table.logger.info("player {0} auto pass".format(p.seat))
                p.del_prompt()
                p.machine.next_state()
                player.table.player_actions.append(p.uuid)

            if player_action_rule == 'DiscardWinRule' and p.seat in player.table.win_seat_prompt and \
                    p.uuid not in player.table.player_actions:
                player.table.player_actions.append(p.uuid)
                if p.seat not in p.table.win_seat_action:
                    p.table.win_seat_action.append(p.seat)
        player.table.is_all_players_do_action()


def dealer_choose(player, proto):
    if player.seat == player.table.dealer_seat and player.seat == player.table.spy_chair:
        choose_code = proto.choose_code
        if choose_code not in [1, 2]:
            player.table.logger.fatal("choose_code : {0} wrong".format(choose_code))
        else:
            player.table.land_lord_chairs = []
            player.table.farmer_chairs = []
            player.table.land_lord_chairs.append(player.seat)
            if choose_code == 1:
                # 一打四
                player.table.spy_chair = -1
            elif choose_code == 2:
                # 叫狗腿
                # 换狗腿牌
                result = player.table.change_spy_card()
                if result:
                    # 换狗腿座位
                    player.table.change_spy_chair()
                    # 地主阵营
                    player.table.land_lord_chairs.append(player.table.spy_chair)
                else:
                    player.table.logger.fatal("Change spy_card Wrong")
                    # 要是实在是找不到狗腿牌就直接判定为一打四
                    player.table.spy_chair = -1
            if player.table.spy_chair == -1:
                player.table.replay["procedure"].append({"dealer_choose": 1})
            else:
                player.table.replay["procedure"].append({"dealer_choose": 2})
            for e_player in player.table.player_dict.values():
                if e_player.seat not in player.table.land_lord_chairs:
                    # 农民阵营
                    player.table.farmer_chairs.append(e_player.seat)

            # 发送选择结果
            if player.table.spy_card != "8G":
                proto_res = game_pb2.PokerDealerChooseResponse()
                proto_res.choose_code = 2
                proto_res.spy_card = player.table.spy_card
                player.table.replay["procedure"].append({"change_goutui": player.table.spy_card})
                for e_player in player.table.player_dict.values():
                    send(POKER_DEALER_CHOOSE, proto_res, e_player.session)
            from rules.player_rules.manager import PlayerRulesManager
            for player in player.table.player_dict.values():
                PlayerRulesManager().condition(player, PLAYER_RULE_CHOOSE)
        # print player.table.farmer_chairs
        # print player.table.land_lord_chairs
