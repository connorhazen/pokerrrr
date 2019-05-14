# coding: utf-8
from algorithm.card_type.main import match_type
from algorithm.compare.main import type_compare
from algorithm.config import POWER_LEVEL
from settings import game_id


def compare(player, cards, card_type=None):
    """ 本次出牌 与上家对比
    Args:
        cards : 本次出牌列表

        card_type : 本次牌形
    Returns:
        1->大于 0->相等 -1->小于 -2->不通过
    """

    activity_card = player.table.active_card
    activity_card_type = player.table.active_card_type
    # print 123
    if not activity_card:
        return 1
    # 地主一打四狗腿八大于所有牌
    if cards == ['8G'] and player.table.spy_chair == -1:
        return 1

    if activity_card == ['8G'] and player.table.spy_chair == -1:
        return -2

    if player.table.active_seat != player.seat:
        return -2

    if not card_type:
        card_type = match_type(cards, game_id)

    level = POWER_LEVEL[game_id].get(card_type, 1)
    ex_level = POWER_LEVEL[game_id].get(activity_card_type, 1)
    if level > ex_level:
        return 1
    # 比较炸弹,两次牌型不同在这比较，牌型相同到type_compare内比较
    # 现在是王炸，之前是炸弹
    if card_type == 'jackBomb' and player.table.active_card_type == 'bomb':
        if len(cards) == 6:
            return 1
        if len(cards) == 5 and len(activity_card) <= 8:
            return 1
        if len(cards) == 4 and len(activity_card) <= 7:
            return 1
        if len(cards) == 3 and list(set(cards)) == ['BB'] and len(activity_card) <= 6:
            return 1
        if len(cards) == 3 and list(set(cards)) == ['SS'] and len(activity_card) <= 5:
            return 1
        return -2
    if card_type == 'bomb' and player.table.active_card_type == 'jackBomb':
        if len(cards) == 12 and len(activity_card) < 6:
            return 1
        if len(cards) in range(9, 12) and len(activity_card) <= 5:
            return 1
        if len(cards) == 8 and len(activity_card) <= 4:
            return 1
        if len(cards) == 7 and len(activity_card) == 3:
            return 1
        if len(cards) == 6 and len(activity_card) == 3 and list(set(activity_card)) == ['SS']:
            return 1
        return -2

    if activity_card_type != card_type:
        return -2

    if len(cards) != len(player.table.active_card) and card_type not in ['jackBomb', 'bomb']:
        return -2

    response = type_compare(game_id, cards, activity_card, card_type)

    return response


if __name__ == '__main__':
    pass
