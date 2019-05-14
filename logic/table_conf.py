# coding: utf-8
import json


class TableConf(object):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.settings = json.loads(kwargs)
        self.chairs = self.settings.get("chairs", 5)
        self.max_rounds = self.settings.get("max_rounds", 10)
        self.game_type = self.settings.get("game_type", 1)
        self.app_id = self.settings.get("app_id")
        self.options = self.settings.get("options")
        self.chips = self.settings.get("chips")
        self.aa = self.settings.get("aa", False)
        # 0-不翻倍 1-翻倍
        self._has_double = self.settings.get('has_double', 0)
        # 1-经典斗地主 2-欢乐斗地主
        self._play_type = self.settings.get('play_type', 1)
        # 封顶倍数 0-不封顶 16/32/64
        self._times_limit = self.settings.get('times_limit', 0)
        # 1-可明牌 0-不明牌
        self._has_show = self.settings.get('has_show', 1)
        # 炸弹算分个数上限 0不上限
        self._max_bomb = self.settings.get('max_bomb', 0)

        # 带喜不带喜 1带喜2不带喜
        self._reward_type = self.settings.get('reward_type', 1)
        # 底分 1/2/3/5
        self._base_score = self.settings.get('base_score', 1)
        # 1可以聊天，2不可以
        self._has_chat = self.settings.get('has_chat', 1)

    def is_aa(self):
        return self.aa

    @property
    def has_chat(self):
        return self._has_chat == 1

    @property
    def reward_type(self):
        return self._reward_type == 1

    @property
    def has_double(self):
        return self._has_double

    @property
    def has_show(self):
        return self._has_show

    @property
    def max_bomb(self):
        return self._max_bomb

    @property
    def times_limit(self):
        return self._times_limit
        # return 32

    @property
    def base_score(self):
        return self._base_score

    @property
    def play_type(self):
        return self._play_type

    @property
    def show_card_config(self):
        """ interval_time : (1,发牌前2s) (2,发牌4s) (3,发牌后3s)
            show_card_double : 阶段:倍数
        """
        data = {
            'interval_time': [(1, 2), (2, 4), (3, 3)],
            'double': {11: 5, 21: 5, 22: 4, 23: 3, 24: 2, 31: 2},
        }
        return data
