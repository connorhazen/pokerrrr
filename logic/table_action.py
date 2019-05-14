# coding: utf-8
# from logic.player_action import calculate_final_score
# from logic.player_action import calculate_final_score
from state.table_state.double import DoubleState
from state.table_state.end import EndState
from state.table_state.rob import RobState
from state.table_state.show_card import ShowCardState
from state.table_state.step import StepState
from state.table_state.dealer_choose import DealerChooseState


def step(table):
    # print 'table_state step : ',table.machine.cur_state.name
    table.machine.trigger(StepState())


def skip_show_card(table):
    for player in table.player_dict.values():
        if player.state != "ShowCardState":
            return
    table.machine.trigger(ShowCardState())


def skip_step(table):
    for player in table.player_dict.values():
        if player.state != "WaitState":
            return
    table.machine.trigger(StepState())


def skip_rob(table):
    for player in table.player_dict.values():
        if player.state != "RobState":
            return
    table.machine.trigger(RobState())


def skip_double(table):
    for player in table.player_dict.values():
        if player.state != "DoubleState":
            return
    table.machine.trigger(DoubleState())


def skip_choose(table):
    for player in table.player_dict.values():
        if player.state != "DealerChooseState":
            return
    table.machine.trigger(DealerChooseState())


def end(table):
    if not table.all_prompt_list and table.win_type:
        table.machine.trigger(EndState())
