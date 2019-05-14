# coding: utf-8
import sys
sys.path.append('/Users/yuzy/Documents/work/lemon_poker/server')

from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient,HTTPClient
from tornado.options import options

from protocol import game_pb2
import uuid
import json
import hashlib
from StringIO import StringIO
import traceback

class WebRequest(object):
    def __init__(self, room_id):
        self.room_id = room_id
        self.room_uuid = '7a6e7a155c0c4928accd5eaef3625e6e'
        self.server_url = 'http://192.168.1.127:8999'

    def post(self, url, body, retry=False):
        try:
            request = HTTPClient()
            response = request.fetch(url, method="POST", body=body)
        except Exception:
            fp = StringIO()
            traceback.print_exc(file=fp)

    def create_room(self, owner):
        proto_web = game_pb2.CreateRoomRequest()
        proto_web.owner = owner
        proto_web.room_uuid = self.room_uuid
        proto_web.kwargs = json.dumps({
                "chairs" : 5,
                "play_type" : 2,
                "max_rounds" : 2,
                "game_type" : 2,
                "app_id" : 2,
                "options" : 0,
                "chips" : 3,
                "aa" : False,
                "game_id": 1,
            })
        url = self.server_url + "/web/create_room"
        body = proto_web.SerializeToString()
        self.post(url, body)

if __name__ == '__main__':
    wr = WebRequest(100001)
    wr.create_room('7a6e7a155c0c4928accd5eaef3625e6e')


