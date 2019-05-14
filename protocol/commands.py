# coding: utf-8

""" 通用麻将命令 0x0001 ~ 0x0FFF """
ENTER_ROOM = 0x0001                   # 进入房间 原命令号（0x1005）
ENTER_ROOM_OTHER = 0x0002             # 其他玩家进入房间 原命令号（0x1015）
EXIT_ROOM = 0x0003                    # 退出房间 原命令号（0x1007）
DISMISS_ROOM = 0x0004                 # 解散房间 原命令号（0x1006）
SPONSOR_VOTE = 0x0005                 # 发起投票解散 原命令号（0x1009）
VOTE = 0x0007                         # 玩家选择投票 原命令号（0x1037）
ONLINE_STATUS = 0x0008                # 在线状态广播 原命令号（0x1016）

SPEAKER = 0x0009                      # 超级广播命令 原命令号（0x1002）
READY = 0x000A                        # 准备 原命令号（0x1012）
DEAL = 0x000B                         # 起手发牌 原命令号（0x2005）
DRAW = 0x000C                         # 摸牌 原命令号（0x1024）
DISCARD = 0x000D                      # 出牌 原命令号（0x1021）
SYNCHRONISE_CARDS = 0x000E            # 服务端主动同步手牌 原命令号（0x1011）
HEARTBEAT = 0x000F            		  # 服务端主动检测心跳

""" 大连穷胡 0x1000 ~ 0x101F """
RECONNECT = 0x1000                    # 玩家断线重连 原命令号（0x1014）
PROMPT = 0x1001                       # 操作提示 原命令号（0x2007）
ACTION = 0x1002                       # 玩家根据提示列表选择动作 原命令号（0x1022）
READY_HAND = 0x1003                   # 听牌提示 原命令号（0x1033）
NIAO = 0x1004                         # 抓鸟 原命令号（0x1026）
SETTLEMENT_FOR_ROUND = 0x1005         # 小结算 原命令号（0x2004）
SETTLEMENT_FOR_ROOM = 0x1006          # 大结算 原命令号（0x2006）
NOTIFY_MSG = 0x1007

""" 长沙麻将 0x1020 ~ 0x103F """
KG = 0x1020                           # 开杠
HD_NOTICE = 0x1021                    # 通知海底
HD_SELECT = 0x1022                    # 玩家回复是否要海底
ACTION_CS = 0x1023                    # 玩家动作
FOLD = 0x1024                         # 小胡收牌
SETTLEMENT_FOR_ROUND_CS = 0x1025      # 小结算
SETTLEMENT_FOR_ROOM_CS = 0x1026       # 大结算
HD_BROADCAST = 0x1027                 # 广播海底牌
PROMPT_CS = 0x1028                    # 提示
FROZEN_CS = 0x1029                    # 表示已经开杠 只能摸牌打牌或者胡牌
DRAW_CS = 0x102A					  # 合并后的摸牌命令
DISCARD_CS = 0x102B					  # 合并后的出牌命令
DEAL_CS = 0x102C					  # 发牌

""" 卡五星 0x1040 ~ 0x105F """
PIAO_SELECTOR = 0x1040                # 广播选漂
PIAO = 0x1041                         # 玩家选漂
ACTION_K5X = 0x1042                   # 玩家动作
PROMPT_K5X = 0x1043                   # 卡五星提示
RECONNECT_K5X = 0x1044                # 卡五星重连
POINTS_MAP = 0x1045                   # 卡五星牌型番数对照
SETTLEMENT_FOR_ROUND_K5X = 0x1046     # 小结算
SETTLEMENT_FOR_ROOM_K5X = 0x1047      # 大结算
MAIMA = 0x1048                        # 买码
SYNC_KONG_SCORE = 0x1049              # 实时同步杠的分数


SHOW_CARD_STEP = 0x2000    # 发牌(明牌)推送<q>
SHOWCARD = 0x2001          # 明牌请求<qh>
SHOWCARD_DEALER = 0x2002   # 地主是否明牌推送<qh>
ROB_DEALER_INIT = 0x2003   # 抢地主推送<q>
ROB_DEALER = 0x2004        # 经典请地主请求推送<qh>
POKER_DOUBLE_INIT = 0x2005 # 进入翻倍推送<q>
POKER_DOUBLE = 0x2006      # 翻倍请求推送<qh>
NOTIFY_DISCARD = 0x2007     # 出牌提醒 
ROB_DEALER_HAPPY = 0x2008   # 欢乐抢地主<qh>
POKER_SYNCHRONISE_CARDS = 0x2009  # 服务器主动同步手牌
POKER_DISCARD = 0x200A 		# 出牌命令
POKER_DEAL = 0x200B  		# 扑克起手发牌
POKER_SETTLEMENT_FOR_ROUND = 0x200C  # 扑克小结算
POKER_SETTLEMENT_FOR_ROOM = 0x200D  # 扑克大结算
POKER_SCORE = 0x200E  # 扑克面板显示分
POKER_RECONNECT = 0x200F  # 扑克重连

POKER_REWARD = 0x2012  # 喜钱通知
POKER_SHOW_CARDS_INIT = 0x2013  # 明牌提醒
POKER_SHOW_CARDS_RESULT = 0x2014  # 明牌结果
POKER_EXPOSE = 0x2015  # 狗腿暴露
POKER_DEALER_CHOOSE_INIT = 0x2016  # 地主选择一打四还是选狗腿
POKER_DEALER_CHOOSE = 0x2017  # 地主选择返回
