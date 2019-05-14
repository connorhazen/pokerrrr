# coding: utf-8
from algorithm.compare.land_lords import LandLordsCompare

def type_compare(game_id, cards, last_cards, card_type):    
    """ 同牌形对比
    Returns:
        1->大于 0->相等 -1->小于
    """
    # 斗地主 
    # if game_id == 10:
    Compare = LandLordsCompare(cards, last_cards)
    compare = getattr(Compare, 'compare_{}'.format(card_type))
    response = compare()
    return response


if __name__ == '__main__':
    cards = ['33','33','33','44','44','44','77','77','88','88']
    last_cards = ['33','33','33','44','44','44','77','77','88','88']
    card_type = 'plane'
    print type_compare(1, cards, last_cards, card_type)