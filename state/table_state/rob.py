# coding: utf-8
import time
from tornado.ioloop import IOLoop

from protocol import game_pb2
from protocol.commands import ROB_DEALER_INIT
from state.table_state.base import TableStateBase
from protocol.serialize import send
import random



class RobState(TableStateBase):
    def __init__(self):
        super(RobState, self).__init__()

    def enter(self, owner):
        super(RobState, self).enter(owner)

        if owner.rob_seat == -1:
            owner.rob_seat = random.randint(0, owner.chairs-1)
            #owner.init_rob_seat = owner.rob_seat
        else:
            owner.rob_seat = owner.seat_dict[owner.rob_seat].next_seat

        if not owner.conf.has_show:
            # 无明牌添加2秒延迟
            now = time.time()
            owner.temp_timer = IOLoop().instance().add_timeout(
                now + 2, self.send_rob_init, owner)
        else:
            self.send_rob_init(owner)

    def send_rob_init(self,owner):
        if owner.temp_timer:
            IOLoop().instance().remove_timeout(owner.temp_timer)
            owner.temp_timer = None
        for k, v in owner.player_dict.items():
            proto = game_pb2.RobLandLordInitResponse()
            proto.uuid = owner.seat_dict[owner.rob_seat].uuid
            proto.play_type = owner.conf.play_type
            send(ROB_DEALER_INIT, proto, v.session)
        owner.dumps()

    def execute(self, owner, event):
        super(RobState, self).execute(owner, event)
        from logic.table_action import skip_double, skip_step
        if event == "skip_double":
            skip_double(owner)
        elif event == "skip_step":
            skip_step(owner)
