# coding: utf-8
# 斗地主
from algorithm.card_type.base_type import BaseType
from collections import Counter


class LandLordsType(BaseType):
    def __init__(self):
        super(LandLordsType, self).__init__()

    def oneCard(self, cards):
        """ 是否单张
        """
        return len(cards) == 1

    def bomb(self, cards):
        """ 判断是否炸弹
        """
        cards = self.exchange(cards)
        return len(set(cards)) == 1

    def jackBomb(self, cards):
        """ 是否王炸
        """
        cards = self.exchange(cards)
        # 两个大小王也算王炸
        if sorted(cards) == sorted([16, 16, 17, 17]):
            return True
        lis = Counter(cards)
        result = False
        for r, num in lis.most_common():
            if r not in [16, 17]:
                return False
            if num == 3:
                result = True
        if result:
            return True
        return False

    def pairs(self, cards):
        """ 是否一对 
        """
        cards = self.exchange(cards)
        return len(set(cards)) == 1

    def straight(self, cards):
        """ 是否顺子
        """
        if len(cards) < 5:
            return False
        lis = Counter(cards)
        most_count = lis.most_common(1)[0][1]
        for r, num in lis.most_common():
            if num != most_count:
                return
        cards = self.exchange(cards)
        if self.has_card(cards, [15, 16, 17]):
            return False
        if len(set(cards)) != len(cards):
            return False
        cards.sort()
        if cards[-1] - cards[0] == (len(cards) - 1):
            return True
        return False

    def threeWithNo(self, cards):
        """ 是否单出3张 
        """
        cards = self.exchange(cards)
        return len(set(cards)) == 1

    def threeMulti(self, cards):
        """ 是否多三连张 333444555 (飞机不带翅膀)
        """
        cards = self.exchange(cards)
        if self.has_card(cards, [15, 16, 17]):
            return False
        lis = Counter(cards)
        lis_r = []
        for r, num in lis.most_common():
            if num != 3:
                return False
            lis_r.append(r)
        # 先排序再计算
        lis_r.sort()
        if lis_r[-1] - lis_r[0] != (len(lis_r) - 1):
            return False
        return True

    def threeWithTwo(self, cards):
        """ 是否三带二
        """
        if len(cards) != 5:
            return False
        cards = self.exchange(cards)
        lis = Counter(cards)
        if len(lis) != 2:
            return False
        for r, num in lis.most_common():
            if num not in [3, 2]:
                return False
        return True

    def threeWithOne(self, cards):
        """ 是否三带一
        """
        if len(cards) != 4:
            return False
        cards = self.exchange(cards)
        lis = Counter(cards)
        if len(lis) != 2:
            return False
        for r, num in lis.most_common():
            if num not in [3, 1]:
                return False
        return True

    def fourWithTwo(self, cards):
        """ 是否四带二
        单独是4张带2单张或一对
        """
        if len(cards) != 6:
            return False
        cards = self.exchange(cards)
        lis = Counter(cards)
        if len(lis) != 3 and len(lis) != 2:
            return False
        if self.has_card(cards, [16]):
            if self.has_card(cards, [17]):
                return False
        has_four = 0
        for r, num in lis.most_common():
            if num == 4:
                has_four += 1
            if num not in [4, 1] and num not in [4, 2]:
                return False
        if not has_four:
            return False
        return True

    def fourWithOne(self, cards):
        """ 是否四带一 
        """
        if len(cards) != 5:
            return False
        cards = self.exchange(cards)
        lis = Counter(cards)
        if len(lis) != 2:
            return False
        for r, num in lis.most_common():
            if num not in [4, 1]:
                return False
        return True

    def pairsStraight(self, cards):
        """ 是否多顺子 334455
        """
        cards = self.exchange(cards)
        lis = Counter(cards)
        most_count = lis.most_common(1)[0][1]
        for r, num in lis.most_common():
            if num != most_count:
                return
        if self.has_card(cards, [15, 16, 17]):
            return False
        res = divmod(len(cards), 2)
        set_lis = list(set(cards))
        if res[1] or len(set_lis) != res[0]:
            return False
        set_lis.sort()
        if set_lis[-1] - set_lis[0] != (len(set_lis) - 1):
            return False
        return True

    # def plane(self, cards):
    #     """ 是否飞机 33344422
    #     """
    #     if len(cards) < 6:
    #         return False
    #     cards = self.exchange(cards)
    #     p1 = []
    #     p2 = []
    #     lis = Counter(cards)
    #     for r, num in lis.most_common():
    #         if num >= 4:
    #             return False
    #         elif num == 3:
    #             p1.append(r)
    #         else:
    #             p2.append(num)
    #     # 不带大小王
    #     if self.has_card(cards, [16]):
    #         if self.has_card(cards,[17]):
    #             return False
    #     p1_length = len(p1)
    #     if p1_length <= 1 :
    #         return False
    #     p1_sort = sorted(p1)
    #     if p1_length <=3 or (p1_length > 3 and sum(p2) == p1_length)or p1_length == len(p2):
    #         #333444555889
    #         for i in range(p1_length-1):
    #             if p1_sort[i+1] - p1_sort[i] != 1:
    #                 return False
    #         if not p2:
    #             return False
    #         if  p1_length == len(p2):
    #             if len(list(set(p2)))!=1:
    #                 return False
    #         if p1_length == sum(p2) :
    #             return True
    #     else:
    #         if not p2:
    #             continuous = []
    #             # 333444555777 333555666777
    #             for i in range(p1_length-1):
    #                 # 222算翅膀
    #                 if p1_sort[i+1]!=15:
    #                     if p1_sort[i + 1] - p1_sort[i] == 1:
    #                         continuous.append(p1_sort[i])
    #                         continuous.append(p1_sort[i+1])
    #             continuous = list(set(continuous))
    #             if len(continuous) != 3*(p1_length-len(continuous)):
    #                 return False
    #             else :
    #                 return True
    #         else:
    #             if len(p2) < p1_length :
    #                 # 333444555666 8999
    #                 continuous = []
    #                 rest = []
    #                 for i in range(p1_length - 1):
    #                     # 222算翅膀
    #                     if p1_sort[i + 1] != 15:
    #                         if p1_sort[i + 1] - p1_sort[i] == 1:
    #                             continuous.append(p1_sort[i])
    #                             continuous.append(p1_sort[i + 1])
    #                 continuous = list(set(continuous))
    #                 rest = list(set(p1)-set(continuous))
    #                 if len(rest) == 0:
    #                     return False
    #                 if len(rest)*3+sum(p2) != p1_length-len(rest):
    #                     return False
    #                 else :
    #                     return True
    #     return False

    def fourWithTwoDouble(self, cards):
        """ 是否四带两对
        """
        if len(cards) != 8:
            return False
        cards = self.exchange(cards)
        lis = Counter(cards)
        if len(lis) != 3:
            return False
        for r, num in lis.most_common():
            if num not in [4, 2]:
                return False
        return True

    def plane(self, cards):
        """ 是否飞机 3334445566
        新规则必须带对子
        三张为2时，带的对子必须相连
        三张为3及以上时，带的对子无要求
        大小王可以当翅膀
        """
        if len(cards) < 10:
            return False
        cards = self.exchange(cards)
        p1 = []
        p2 = []
        lis = Counter(cards)
        for r, num in lis.most_common():
            if num == 3:
                p1.append(r)
            else:
                p2.append(num)
        # 不带大小王
        # if self.has_card(cards, [16]):
        #     if self.has_card(cards, [17]):
        #         return False
        p1_length = len(p1)
        if p1_length <= 1:
            return False
        p1_sort = sorted(p1)
        # 取连串的三张
        continuous = []
        for i in range(p1_length - 1):
            # 222算翅膀
            if p1_sort[i + 1] not in [15, 16, 17]:
                if p1_sort[i + 1] - p1_sort[i] == 1:
                    continuous.append(p1_sort[i])
                    continuous.append(p1_sort[i + 1])
                else:
                    return False
            else:
                return False
        continuous = list(set(continuous))
        if not p2:
            return False
        else:
            # 如果三张里没有翅膀
            if len(continuous) == p1_length:
                if p1_length == 2:
                    # 单独处理三张为2时，带的对子必须相连
                    if list(set(p2)) == [2]:
                        if len(p2) == p1_length:
                            test_2 = []
                            for r, num in lis.most_common():
                                if num == 2:
                                    test_2.append(r)
                            test_2.sort()
                            for cc in [15, 16, 17]:
                                if cc in test_2:
                                    return False
                            if test_2[-1] - test_2[0] == 1:
                                return True
                    return False
                # 全对牌
                else:
                    for count in p2:
                        if count % 2 != 0:
                            return False
                    if sum(p2) / 2 == p1_length:
                        return True
                    else:
                        return False
            else:
                # 三张里有翅膀
                return False

    # 单张、对子、三张、三带二、连对、三顺（飞机不带翅膀）、飞机、炸弹、王炸
    def get_type(self, cards):
        length = len(cards)
        if length == 1:
            # 单张
            trees = [self.oneCard]
        elif length == 2:
            # 对子
            trees = [self.pairs]
        elif length == 3:
            # 王炸、三张
            trees = [self.jackBomb, self.threeWithNo]
        elif length == 4:
            # 王炸、炸弹
            trees = [self.jackBomb, self.bomb]
        elif length == 5:
            # 王炸、三带二
            trees = [self.jackBomb, self.threeWithTwo, self.bomb]
        elif length == 6:
            # 连对、王炸、三顺
            trees = [self.pairsStraight, self.jackBomb, self.threeMulti, self.bomb]
        else:
            # 连对、飞机、三连
            trees = [self.pairsStraight, self.plane, self.threeMulti, self.bomb]

        for action in trees:
            if action(cards):
                # return action.func_name
                return action.__name__
        return None


if __name__ == '__main__':
    # pass
    # 测试用例
    # print LandLordsType().get_type(['TT', 'TT', 'TT', 'TT', 'TT'])
    # print LandLordsType().get_type(['BB', 'BB', 'BB'])
    # print LandLordsType().get_type(['5r'])
    # print LandLordsType().get_type(['Kr'])
    # print LandLordsType().get_type(['3r', '3r'])
    # print LandLordsType().get_type(['Ar', 'Ar'])
    # print LandLordsType().get_type(['3r', '3r', '3r'])
    # print LandLordsType().get_type(['Jr', 'Jr', 'Jr'])
    # print LandLordsType().get_type(['6r', '6q', '6e', '2e'])
    # print LandLordsType().get_type(['Tr', 'Tq', 'Te', '9e'])
    # print LandLordsType().get_type(['6r', '6q', '6e', '2e', '2e'])
    # print LandLordsType().get_type(['Tr', 'Tq', 'Te', '4e', '4e'])
    # print LandLordsType().get_type(['3r', '3q', '3e', '3e', '7e', '8e'])
    # print LandLordsType().get_type(['6r', '6q', '6e', '6e', '4e', '5e'])
    # print LandLordsType().get_type(['8r', '8q', '8e', '8e', '6e', '6e', '5e', '5e'])
    # print LandLordsType().get_type(['Tr', 'Tq', 'Te', 'Te', '6e', '6e', '5e', '5e'])
    # print LandLordsType().get_type(['4r', '5q', '6e', '7e', '8e'])
    # print LandLordsType().get_type(['8r', '9q', 'Te', 'Je', 'Qe'])
    # print LandLordsType().get_type(['6r', '7q', '8e', '9e', 'Te', 'Je'])
    # print LandLordsType().get_type(['9r', 'Tq', 'Je', 'Qe', 'Ke', 'Ae'])
    # print LandLordsType().get_type(['3r', '4q', '5e', '6e', '7e', '8e', '9e'])
    # print LandLordsType().get_type(['5r', '6q', '7e', '8e', '9e', 'Te', 'Je'])
    # print LandLordsType().get_type(['3r', '4q', '5e', '6e', '7e', '8e', '9e', 'Ta'])
    # print LandLordsType().get_type(['4r', '5q', '6e', '7e', '8e', '9e', 'Te', 'Ja'])
    # print LandLordsType().get_type(['3r', '4q', '5e', '6e', '7e', '8e', '9e', 'Ta', 'Je'])
    # print LandLordsType().get_type(['4r', '5q', '6e', '7e', '8e', '9e', 'Te', 'Ja', 'Qe'])
    # print LandLordsType().get_type(['3r', '4q', '5e', '6e', '7e', '8e', '9e', 'Ta', 'Je', 'Qe'])
    # print LandLordsType().get_type(['4r', '5q', '6e', '7e', '8e', '9e', 'Te', 'Ja', 'Qe', 'Ke'])
    # print LandLordsType().get_type(['3r', '4q', '5e', '6e', '7e', '8e', '9e', 'Ta', 'Je', 'Qe', 'Ke'])
    # print LandLordsType().get_type(['4r', '5q', '6e', '7e', '8e', '9e', 'Te', 'Ja', 'Qe', 'Ke', 'Ae'])
    # print LandLordsType().get_type(['4r', '4q', '5e', '5e', '6e', '6e'])
    # print LandLordsType().get_type(['9r', '9q', 'Te', 'Te', 'Je', 'Je'])
    # print LandLordsType().get_type(['5r', '5q', '6e', '6e', '7e', '7e', '8e', '8e'])
    # print LandLordsType().get_type(['9r', '9q', 'Te', 'Te', 'Je', 'Je', 'Qe', 'Qe'])
    # print LandLordsType().get_type(['7r', '7q', '8e', '8e', '9e', '9e', 'Te', 'Te', 'Je', 'Je'])
    # print LandLordsType().get_type(['9r', '9q', 'Te', 'Te', 'Je', 'Je', 'Qe', 'Qe', 'Ke', 'Ke'])
    # print LandLordsType().get_type(['5r', '5q', '6e', '6e', '7e', '7e', '8e', '8e', '9e', '9e', 'Te', 'Te'])
    # print LandLordsType().get_type(['6r', '6q', '7e', '7e', '8e', '8e', '9e', '9e', 'Te', 'Te', 'Je', 'Je'])
    # print LandLordsType().get_type(['4r', '4q', '5e', '5e', '6e', '6e', '7e', '7e', '8e', '8e', '9e', '9e', 'Te', 'Te'])
    # print LandLordsType().get_type(['8r', '8q', '9e', '9e', 'Te', 'Te', 'Je', 'Je', 'Qe', 'Qe', 'Ke', 'Ke', 'Ae', 'Ae'])
    # print LandLordsType().get_type(
    #     ['3r', '3q', '4e', '4e', '5e', '5e', '6e', '6e', '7e', '7e', '8e', '8e', '9e', '9e', 'Te', 'Te'])
    # print LandLordsType().get_type(
    #     ['6r', '6q', '7e', '7e', '8e', '8e', '9e', '9e', 'Te', 'Te', 'Je', 'Je', 'Qe', 'Qe', 'Ke', 'Ke'])
    # print LandLordsType().get_type(['5r', '5q', '5e', '6e', '6e', '6e'])
    # print LandLordsType().get_type(['Qr', 'Qq', 'Qe', 'Ke', 'Ke', 'Ke'])
    # print LandLordsType().get_type(['9r', '9q', '9e', 'Te', 'Te', 'Te', 'Je', 'Je', 'Je'])
    # print LandLordsType().get_type(['Qr', 'Qq', 'Qe', 'Ke', 'Ke', 'Ke', 'Ae', 'Ae', 'Ae'])
    # print LandLordsType().get_type(['7r', '7q', '7e', '8e', '8e', '8e', '9e', '9e', '9e', 'Te', 'Te', 'Te'])
    # print LandLordsType().get_type(['8r', '8q', '8e', '9e', '9e', '9e', 'Te', 'Te', 'Te', 'Je', 'Je', 'Je'])
    # print LandLordsType().get_type(['4r', '4q', '4e', '5e', '5e', '5e', '9e', '9e'])
    # print LandLordsType().get_type(['Kr', 'Kq', 'Ke', 'Ae', 'Ae', 'Ae', '5e', '6e'])
    # print LandLordsType().get_type(['5r', '5q', '5e', '6e', '6e', '6e', '4e', '4e', 'Ae', 'Ae'])
    # print LandLordsType().get_type(['8r', '8q', '8e', '7e', '7e', '7e', '4e', '4e', 'Ae', 'Ae'])
    # print LandLordsType().get_type(['9r', '9q', '9e', 'Te', 'Te', 'Te', 'Je', 'Je', 'Je', '6e', '7e', '8e'])
    # print LandLordsType().get_type(['Tr', 'Tq', 'Te', 'Je', 'Je', 'Je', 'Qe', 'Qe', 'Qe', '5e', '5e', '4e'])
    # print LandLordsType().get_type(
    #     ['9r', '9q', '9e', 'Te', 'Te', 'Te', 'Je', 'Je', 'Je', '4e', '4e', '5e', '5e', '6e', '6e'])
    # print LandLordsType().get_type(
    #     ['Jr', 'Jq', 'Je', 'Qe', 'Qe', 'Qe', 'Ke', 'Ke', 'Ke', 'Ae', 'Ae', '8e', '8e', '9e', '9e'])
    # print LandLordsType().get_type(
    #     ['8r', '8q', '8e', '9e', '9e', '9e', 'Te', 'Te', 'Te', 'Je', 'Je', 'Je', '6e', '7e', '8e', '9e'])
    # print LandLordsType().get_type(
    #     ['Jr', 'Jq', 'Je', 'Qe', 'Qe', 'Qe', 'Ke', 'Ke', 'Ke', 'Ae', 'Ae', 'Ae', '3e', '5e', '7e', '9e'])
    # print LandLordsType().get_type(['5r', '5q', '5e', '5e'])
    # print LandLordsType().get_type(['Kr', 'Kq', 'Ke', 'Ke'])
    # print LandLordsType().get_type(['55', '55', '55', '66', '66', '66', '77', '77', '88', '88'])
    # print LandLordsType().get_type(['55', '55', '55', '55', '66', '66', '66', '77'])
    print LandLordsType().get_type(['55', '55', '55', '55', '66', '66', '66', '66', '77', '77', '77'])
