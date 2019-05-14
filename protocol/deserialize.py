# coding: utf-8

import struct

from logic.session_manager import SessionMgr
from logic.table_manager import TableMgr
from protocol import game_pb2
from protocol.commands import *
from protocol.serialize import send
from utils.logger import Logger

logger = Logger("exception")
stick_package_stack = None


# noinspection PyBroadException
def parse(cmd, raw, session):
    try:
        serial_router[cmd](raw, session)
    except Exception:
        import traceback
        from StringIO import StringIO
        f = StringIO()
        traceback.print_exc(file=f)
        logger.fatal(f.getvalue())


# noinspection PyBroadException
def receive(raw, session):
    global stick_package_stack
    try:
        if stick_package_stack:
            raw = stick_package_stack + raw
            stick_package_stack = None
        size, = struct.unpack('>i', raw[:4])
        raw_size = len(raw)
        if raw_size > size:  # 至少有一个包
            cmd, = struct.unpack('>i', raw[4:8])
            string, = struct.unpack('>{0}s'.format(size - 8), raw[8:size])
            parse(cmd, string, session)
            rest = raw[size:]
            receive(rest, session)
        elif size > raw_size:  # 半包
            stick_package_stack = raw
        elif size == raw_size:
            cmd, = struct.unpack('>i', raw[4:8])
            string, = struct.unpack('>{0}s'.format(size - 8), raw[8:size])
            parse(cmd, string, session)
        else:
            pass
    except Exception as e:
        import traceback
        print e
        traceback.print_exc()


def heartbeat(string, session):
    # proto = game_pb2.HeartbeatResponse()
    # proto.ParseFromString(string)
    # session.heartbeats = 0
    pass


def enter_room(string, session):
    # print 'enter_room'
    proto = game_pb2.EnterRoomRequest()
    proto.ParseFromString(string)
    TableMgr().enter(proto.room_id, proto.player, proto.info, session)


def exit_room(string, session):
    # print 'exit_room'
    proto = game_pb2.ExitRoomRequest()
    proto.ParseFromString(string)
    player = SessionMgr().player(session)
    player.exit_room()


def dismiss_room(string, session):
    print 'dismiss_room'
    proto = game_pb2.DismissRoomRequest()
    proto.ParseFromString(string)
    player = SessionMgr().player(session)
    player.dismiss_room()


def vote(string, session):
    # print 'vote'
    proto = game_pb2.PlayerVoteRequest()
    proto.ParseFromString(string)
    player = SessionMgr().player(session)
    player.vote(proto)


def ready(string, session):
    # print 'ready'
    proto = game_pb2.ReadyRequest()
    proto.ParseFromString(string)
    player = SessionMgr().player(session)
    player.machine.cur_state.execute(player, "ready", proto)


def discard(string, session):
    # print 'discard=='
    proto = game_pb2.PokerDiscardRequest()
    proto.ParseFromString(string)
    player = SessionMgr().player(session)
    # for i in proto.cards:
    #     print 1111
    #     i.card.replace("\n","")
    player.machine.cur_state.execute(player, "discard", proto)


def action(string, session):
    # print 'action'
    player = SessionMgr().player(session)
    proto = game_pb2.ActionRequest()
    proto.ParseFromString(string)
    # print 'actionid:', player.uuid, proto.action_id, player.machine.cur_state
    player.machine.cur_state.execute(player, "action", proto)


def rob_dealer(string, session):
    """ 普通抢地主
    """
    player = SessionMgr().player(session)
    proto = game_pb2.RobLandLordRequest()
    proto.ParseFromString(string)
    player.machine.cur_state.execute(player, 'rob_dealer', proto)


def rob_dealer_happy(string, session):
    """ 欢乐抢地主
    """
    player = SessionMgr().player(session)
    proto = game_pb2.RobLandLord2Request()
    proto.ParseFromString(string)
    player.machine.cur_state.execute(player, 'rob_dealer_happy', proto)


def poker_double(string, session):
    """ 翻倍
    """
    player = SessionMgr().player(session)
    proto = game_pb2.PokerDoubleRequest()
    proto.ParseFromString(string)
    player.machine.cur_state.execute(player, 'poker_double', proto)


def show_card(string, session):
    """ 明牌
    """
    player = SessionMgr().player(session)
    proto = game_pb2.PokerShowCardRequest()
    proto.ParseFromString(string)
    if not player.is_show_card_state(session):
        return
    player.machine.cur_state.execute(player, 'show_card', proto)


def show_card_dealer(string, session):
    """ 地主二次明牌
    """
    # player = SessionMgr().player(session)
    # proto = game_pb2.ShowCardRequest()
    # proto.ParseFromString(string)
    # player.machine.cur_state.execute(player, 'show_card_dealer', proto)
    pass


def speaker(string, session):
    player = SessionMgr().player(session)
    # 禁止聊天
    print player.seat
    if not player.table.conf.has_chat:
        return
    proto = game_pb2.SpeakerRequest()
    proto.ParseFromString(string)
    proto_back = game_pb2.SpeakerResponse()
    proto_back.player = player.uuid
    proto_back.content = proto.content

    for i in player.table.player_dict.values():
        send(SPEAKER, proto_back, i.session)


def dealer_choose(string, session):
    player = SessionMgr().player(session)
    proto = game_pb2.PokerDealerChooseRequest()
    proto.ParseFromString(string)
    player.machine.cur_state.execute(player, 'dealer_choose', proto)


serial_router = {
    HEARTBEAT: heartbeat,
    ENTER_ROOM: enter_room,
    EXIT_ROOM: exit_room,
    DISMISS_ROOM: dismiss_room,
    VOTE: vote,
    READY: ready,
    POKER_DISCARD: discard,
    ACTION: action,
    SPEAKER: speaker,
    ROB_DEALER: rob_dealer,
    ROB_DEALER_HAPPY: rob_dealer_happy,
    POKER_DOUBLE: poker_double,
    # SHOWCARD: show_card,
    SHOWCARD_DEALER: show_card_dealer,
    # POKER_SHOW_CARDS_INIT: show_card,
    POKER_SHOW_CARDS_RESULT: show_card,
    POKER_DEALER_CHOOSE: dealer_choose
}


def pack():
    i = struct.pack("ii5shi", 0, 1, "1.0.1", 1, 9)
    print len(i), i
    print struct.unpack("ii5shi", i)


if __name__ == '__main__':
    pack()
