# coding: utf-8

import json

from logic.player import Player
from logic.table import Table
from logic.table_conf import TableConf
from settings import redis
from state.player_state.deal import DealState
from state.player_state.discard import DiscardState
from state.player_state.double import DoubleState
from state.player_state.init import InitState
from state.player_state.pause import PauseState
from state.player_state.prompt import PromptState
from state.player_state.prompt_discard import PromptDiscardState
from state.player_state.prompt_draw import PromptDrawState
from state.player_state.ready import ReadyState
from state.player_state.rob import RobState
from state.player_state.settle import SettleState
from state.player_state.show_card import ShowCardState
from state.player_state.show_card_dealer import ShowCardDealerState
from state.player_state.wait import WaitState
from state.player_state.dealer_choose import DealerChooseState
from state.table_state.deal import DealState as TableDealState
from state.table_state.double import DoubleState as TableDoubleState
from state.table_state.end import EndState as TableEndState
from state.table_state.init import InitState as TableInitState
from state.table_state.ready import ReadyState as TableReadyState
from state.table_state.restart import RestartState as TableRestartState
from state.table_state.rob import RobState as TableRobState
from state.table_state.settle_for_room import SettleForRoomState as TableSettleForRoomState
from state.table_state.settle_for_round import SettleForRoundState as TableSettleForRoundState
from state.table_state.show_card import ShowCardState as TableShowCardState
from state.table_state.step import StepState as TableStepState
from state.table_state.wait import WaitState as TableWaitState
from state.table_state.dealer_choose import DealerChooseState as TableDealerChooseState
from web.request import WebRequest

player_state = {
    "DealState": DealState(),
    "DiscardState": DiscardState(),
    "InitState": InitState(),
    "PauseState": PauseState(),
    "PromptState": PromptState(),
    "PromptDrawState": PromptDrawState(),
    "PromptDiscardState": PromptDiscardState(),
    "ReadyState": ReadyState(),
    "SettleState": SettleState(),
    "WaitState": WaitState(),
    'RobState': RobState(),
    'ShowCardState': ShowCardState(),
    'ShowCardDealerState': ShowCardDealerState(),
    'DoubleState': DoubleState(),
    'DealerChooseState': DealerChooseState()
}

table_state = {
    "DealState": TableDealState(),
    "EndState": TableEndState(),
    "InitState": TableInitState(),
    "ReadyState": TableReadyState(),
    "RestartState": TableRestartState(),
    "SettleForRoomState": TableSettleForRoomState(),
    "SettleForRoundState": TableSettleForRoundState(),
    "StepState": TableStepState(),
    "WaitState": TableWaitState(),
    'RobState': TableRobState(),
    'ShowCardState': TableShowCardState(),
    'DoubleState': TableDoubleState(),
    'DealerChooseState': TableDealerChooseState(),
}


def loads_player(uuid, table):
    raw = redis.get("player:{0}".format(uuid))
    # print "player", uuid, raw
    if not raw:
        return
    data = json.loads(raw)
    player = Player(uuid, None, None, table)
    for k, v in data.items():
        if k in ("table", "session", "machine", "proto"):
            continue
        else:
            player.__dict__[k] = v
    proto = data.get("proto")
    if proto:
        player.proto.__dict__.update(proto)
        player.proto.load()
    state = data["machine"]
    for k, v in player.action_dict.items():
        player.action_dict[int(k)] = v
        del player.action_dict[k]
    player.machine.last_state = player_state[state[0]] if state[0] else None
    player.machine.cur_state = player_state[state[1]] if state[1] else None
    return player


def loads_table(room_id):
    raw = redis.get("table:{0}".format(room_id))
    # print "table", room_id, raw
    if not raw:
        return
    data = json.loads(raw)

    table = Table(room_id, None, None, None)
    for k, v in data.items():
        if k in ("logger", "conf", "player_dict", "seat_dict", "machine", "reward_info"):
            continue
        else:
            table.__dict__[k] = v

    table.conf = TableConf(table.kwargs)
    table.request = WebRequest(room_id, table.room_uuid, table.conf.game_type, table.conf.app_id, table.owner)

    for i in data["player_dict"]:
        table.player_dict[i] = loads_player(i, table)

    for i, j in data["seat_dict"].items():
        table.seat_dict[int(i)] = table.player_dict[j]
    if "reward_info" in data:
        for i, j in data["reward_info"].items():
            table.reward_info[int(i)] = j
    # 设置重连暂停状态
    table.pasue_state = True


    state = data["machine"]
    table.machine.last_state = table_state[state[0]] if state[0] else None
    table.machine.cur_state = table_state[state[1]] if state[1] else None
    return table
