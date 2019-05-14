# coding: utf-8
import random

# 花色 红黑方草 加狗腿花色
SUITS = ['H', 'S', 'D', 'C']

SUITS_GOUTUI = ['G', ]

init_GOUTUI_NUMBER = ['8', ]

# 初始基本牌
INIT_LIST = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
# 大王 小王
INIT_JACK = ['BB', "SS"]


# 单张牌值映射
MAPPING_LIST = '0003456789TJQKA2SB'

# 权级 默认为1
POWER_LEVEL = {
    10:{ # 斗地主
        'jackBomb': 9,
        'bomb': 9,
    }
}
def init_landlords():
    """ 初始化斗地主 54张牌 * 3副牌 = 162
    """
    lis = []
    for card in INIT_LIST:
        for suit in SUITS:
            for i in range(3):
                lis.append('{0}{1}'.format(card, suit))
    lis.extend(INIT_JACK * 3)
    # 移除一张红桃8
    lis.remove('8H')
    # 添加一张狗腿八
    lis.append('8G')
    random.shuffle(lis)
    return lis

if __name__ == '__main__':
    lis = init_landlords()
    lis.sort()
    print lis