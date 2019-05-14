# coding: utf-8
# 斗地主
from algorithm.card_type.land_lords import LandLordsType

def match_type(cards, game_id):
    """ 获取牌形
    """
    # 10-斗地主
    # if game_id == 10:
    type_obj = LandLordsType()
    types = type_obj.get_type(cards)
    return types
    # return


def get_color_count(cards):
    red = 0
    black = 0
    for card in cards:
        # 红桃方片狗腿
        if card[1] in ['H', 'D', 'G']:
            red += 1
        # 黑桃草花
        if card[1] in ['S', 'C']:
            black += 1
    return {'red': red, 'black': black}


