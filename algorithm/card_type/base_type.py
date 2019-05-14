# coding: utf-8
from algorithm.config import MAPPING_LIST


class BaseType(object):

    def exchange(self, cards):
        # 牌提取成数组
        return [MAPPING_LIST.index(r) for r, s in cards]

    def has_card(self, cards, check_card):
        """ 验证牌形中是否有给出的牌
        """
        return bool(filter(lambda x: x in cards, check_card))
