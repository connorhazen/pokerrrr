# coding: utf-8

from collections import defaultdict
from utils.singleton import Singleton

cards_rest = defaultdict(list)


class TableRulesBase(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.name = self.__class__.__name__

    def condition(self, table):
        pass

    def action(self, table):
        pass
