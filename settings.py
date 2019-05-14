# coding: utf-8

import os
from ConfigParser import ConfigParser
import redis as r
from tornado.options import options

port_st = 8291
port_et = 8292
interval = 1000
root = os.path.dirname(__file__)
log_dir = os.path.join(root, "log")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

env = os.environ.get("env", "dev")


if env == "pro":
    token = "landlord game 1"
elif env == "test":
    token = "A4^&*(Sdf65a4@#623$%^465ASD%^*(4F6W20"
else:
    token = ""

redis = r.Redis(host=options.redis_host, port=options.redis_port, password=options.redis_password, db=options.redis_db)

conf_web = ConfigParser()
conf_web.read(os.path.join(os.path.join(root, "confs"), "web.conf"))
# web_alloc_url = "http://alloc.poker.xnny.com"
web_alloc_url = conf_web.get("url", "alloc")
# web_record_url = "http://poker.xnny.com"
web_record_url = conf_web.get("url", "record")

dismiss_delay = 60
heartbeat = 12
# 地主选择时间4改6
choose_delay = 6
show_card_delay = 4

game_id=10



