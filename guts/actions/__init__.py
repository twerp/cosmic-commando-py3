'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.actions.interactive import *
from guts.actions.combat import *

class Action(object):
    '''
    Action objects are needed to wrap action functions.
    They fall into two categories - interactions, where an agent interacts with an interactive piece,
    and operations, where an agent uses the operative piece on a target piece.

    Action data is initialised with 
        1) externally defined piece_data, which contains data
        relevant to the piece the interaction will serve,
        e.g. custom messages to display.
        2) basic data - which is the same for a given interaction,
        no matter what piece it will be attached to.
        Examples: piece data would be something defined for a specific
        kind of a game piece, while basic data would be shared by all
        kinds of game pieces using a given interaction.
    """     
    '''

    def __init__(self, requires_target, action_function, name, data = {}):
        self.function = action_function
        self._data = {}
        self._data.update(data)
        self.piece = None
        self.name = name
        self.requires_target = requires_target
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
        
    def __contains__(self, key):
        return key in self._data

    def execute(self, agent, *args, **kwargs):
        if self.requires_target:
            if 'target' in kwargs:
                target = kwargs['target']
            else:
                target = args[0]
            self.piece['last target'] = target
            return self.function(self, agent, target)
        else:
            return self.function(self, agent)


def new_action(action_name, piece_data):
    data = {}
    data.update(piece_data)
    #function, requires_target, basic_data = actions[action_name]
    if len(actions[action_name]) == 2:
        function, requires_target = actions[action_name]
    else:
        function, requires_target, action_data = actions[action_name]
        data.update(action_data)
    return Action(requires_target, action_function = function, name = action_name, data = data)

#key : (function, requires_target, additional data)    
actions = {'door': (door_manipulation, False),
           'feedback' : (feedback_msg, False),
           'replenish' : (replenish, False),
           'melee' : (melee, True),
           'confusing melee' : (confusing_melee, True),
           'shoot' : (shoot, True),
           'shoot_or_reload': (shoot_or_reload, True),
           'chain lightning' : (chain_lightning, False),
           'use grenade' : (use_grenade, False),
           'throw grenade' : (throw_grenade, True),
           'mark agent' : (mark_agent, True),
           'mission': (mission, False, {'accomplished': False}),
           'flavor': (flavor, False, {'touched': False}),
           'blow up': (blow_up, True),
           'trait transfer': (trait_transfer, False),
           'deploy feature': (deploy_feature, True),
           'scattershoot': (project_cone, True),
           'gunmelee' : (gun_bump_into, True)
          }

__all__ = ['new_action']