'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.debug import debug
from guts.game_data import game
from guts.messages import message
from guts.utils import coinflip, random_pos
from guts.game_piece import Piece
from guts.game_description import trait_level_description

class Terrain(Piece):
    def __init__(self, *args, **kwargs):
        Piece.__init__(self, *args, **kwargs)
            
class Item(Piece):
    
    def __init__(self, *args, **kwargs):
        Piece.__init__(self, *args, **kwargs)

    def use(self, agent, action_type, target = None):
        action = self[action_type]
        if action.requires_target:
            successful_use = action.execute(agent, target)
        else:
            successful_use = action.execute(agent)
            if target is not None:
                debug.log(str.format("Item {0.name} interaction {1.name} received a target: {2.name}", self, self.usage, target))
        return successful_use
        """
        if (successful_use and action_type == 'consumable') or action_type == 'deployable':
            if not 'stack' in self or self['stack'] == 1:
                agent[action_type + ' item'] = None
                agent.inventory.remove(self)
            else:
                self['stack'] -= 1
        if (successful_use and self.flag('limited')):
            agent['special equipment'] -= 1
        """

    def leave(self):
        game.board[self.x, self.y].remove(self)
        
    def _arrive_on(self, tile):
        tile.put(self)
        
class Feature(Piece):
    
    def __init__(self, *args, **kwargs):
        Piece.__init__(self, *args, **kwargs)
        self.interaction = kwargs['interaction']
        if self.interaction is not None:
            self.interaction.piece = self 

    def interact(self, agent):
        self.interaction.execute(agent)

    def leave(self):
        game.board[self.x, self.y].feature = None
        
    def _arrive_on(self, tile):
        tile.feature = self
