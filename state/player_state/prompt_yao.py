# coding: utf-8

from state.player_state.base import PlayerStateBase



class PromptYaoState(PlayerStateBase):

    def enter(self, owner):
        super(PromptYaoState, self).enter(owner)
        owner.table.player_prompts.append(owner.uuid)
        # owner.send_prompts()
        #owner.proto.send()
        owner.table.clear_actions()

    def next_state(self, owner):
        from state.player_state.draw import DrawState
        print 'yao pass'
        owner.machine.trigger(DrawState())

    def execute(self, owner, event, proto=None):
        super(PromptYaoState, self).execute(owner, event, proto)
        from logic.player_action import action
        if event == "action":
            action(owner, proto)
        else:
            owner.table.logger.warn("player {0} event {1} not register".format(owner.seat, event))
