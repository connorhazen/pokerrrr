# coding: utf-8
from collections import Counter

from algorithm.compare.base_compare import BaseCompare


class LandLordsCompare(BaseCompare):

    def __init__(self, cards1, cards2):
        super(LandLordsCompare, self).__init__()

        self.cards1 = self.exchange(cards1)
        self.cards2 = self.exchange(cards2)

    def compare_oneCard(self):
        """ 比较单张
        """
        return cmp(self.cards1[0], self.cards2[0])

    def compare_pairs(self):
        """ 比较对子
        """
        return cmp(self.cards1[0], self.cards2[0])

    def compare_bomb(self):
        """ 比较炸弹
        """
        cards_count = cmp(len(self.cards1), len(self.cards2))
        if cards_count == 0:
            return cmp(self.cards1[0], self.cards2[0])
        else:
            return cards_count

    def compare_jackBomb(self):
        """ 比较王炸
        """
        return cmp(self.cards1[0], self.cards2[0])

    def compare_straight(self):
        """ 比较顺子
        """
        self.cards1.sort()
        self.cards2.sort()
        return cmp(self.cards1[0], self.cards2[0])

    def compare_threeWithNo(self):
        """ 比较三张
        """
        return cmp(self.cards1[0], self.cards2[0])

    def compare_threeMulti(self):
        """ 比较多三连张
        """
        self.cards1.sort()
        self.cards2.sort()
        return cmp(self.cards1[0], self.cards2[0])

    def compare_threeWithTwo(self):
        """ 比较三带二
        """
        c1 = self.count_card(self.cards1, 3)[0]
        c2 = self.count_card(self.cards2, 3)[0]
        return cmp(c1, c2)

    def compare_threeWithOne(self):
        """ 比较三带一
        """
        c1 = self.count_card(self.cards1, 3)[0]
        c2 = self.count_card(self.cards2, 3)[0]
        return cmp(c1, c2)

    def compare_fourWithTwo(self):
        """ 比较四带二
        """
        c1 = self.count_card(self.cards1, 4)[0]
        c2 = self.count_card(self.cards2, 4)[0]
        return cmp(c1, c2)

    def compare_fourWithOne(self):
        """ 比较四带一
        """
        c1 = self.count_card(self.cards1, 4)[0]
        c2 = self.count_card(self.cards2, 4)[0]
        return cmp(c1, c2)

    def compare_pairsStraight(self):
        """ 比较多顺子
        """
        c1 = min(self.cards1)
        c2 = min(self.cards2)
        return cmp(c1, c2)

    def compare_plane(self):
        """ 比较飞机
        """
        continuous1 = self.get_continuous(self.cards1)
        continuous2 = self.get_continuous(self.cards2)
        c1 = continuous1[0]
        c2 = continuous2[0]
        return cmp(c1, c2)

    def compare_fourWithTwoDouble(self):
        """ 比较四带两对
        """
        c1 = self.count_card(self.cards1, 4)[0]
        c2 = self.count_card(self.cards2, 4)[0]
        return cmp(c1, c2)

    def get_continuous(self, cards):
        p1 = []
        lis = Counter(cards)
        for r, num in lis.most_common():
            if num == 3:
                p1.append(r)
        p1_length = len(p1)
        p1_sort = sorted(p1)
        continuous = []
        for i in range(p1_length - 1):
            # 2 大王 小王算翅膀
            if p1_sort[i + 1] not in [15, 16, 17]:
                if p1_sort[i + 1] - p1_sort[i] == 1:
                    continuous.append(p1_sort[i])
                    continuous.append(p1_sort[i + 1])
        continuous = sorted(list(set(continuous)))
        return continuous

    def has_card(self, cards, check_card):
        """ 验证牌形中是否有给出的牌
        """
        return bool(filter(lambda x: x in cards, check_card))


if __name__ == '__main__':
    # LandLordsCompare()
    pass
