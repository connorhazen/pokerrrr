# coding=utf-8
from algorithm.config import MAPPING_LIST, SUITS




def change_spy_chard():
    # dealer = self.seat_dict[self.dealer_seat]
    # 浅拷贝手牌
    # cards = dealer.cards_in_hand[:]
    cards = ['KH', 'KH', '2H', '2H']
    from collections import Counter
    lis = Counter(cards)
    pre_cards = []
    for r, num in lis.most_common():
        # 将数量为2的牌筛选出来，不包含大小王和红桃8
        if num == 2 and r not in ['8H', 'BB', 'SS']:
            pre_cards.append(r)
    pre_cards_num = [MAPPING_LIST.index(r) for r, s in pre_cards]
    pre_cards_num.sort(reverse=True)
    max_num = pre_cards_num[0]
    for suit in SUITS:
        card = MAPPING_LIST[max_num] + suit
        if card in pre_cards:
            # self.spy_card = cards
            print(card)
            break
    return True
def exchange( card):
    # 牌提取成数组
    return MAPPING_LIST.index(card[0])

if __name__ == '__main__':
    # print change_spy_chard()
    print exchange("AAA")
