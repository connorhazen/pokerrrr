# coding: utf-8
from algorithm.config import MAPPING_LIST
from collections import Counter

class BaseCompare(object):

    def exchange(self, cards):
        return [MAPPING_LIST.index(r) for r, s in cards]

    def count_card(self, cards, n):
        """ 返回 cards中 数量为n的牌
        """
        lis = Counter(cards)
        returns = []
        for r, num in lis.most_common():
            if num == n:
                returns.append(r)
                return returns
        return returns



