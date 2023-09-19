'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.game_data import game

class Piece(object):
    
    def __init__(self, shape, color, flags, traits = None, interaction = None):
        self.x = None
        self.y = None
        self.always_visible = False #only useful for debugging
        self.traits = {}
        if traits is not None:
            self.traits.update(traits)
        for flag in flags:
            self.traits[flag] = True
        self.traits['shape'] = shape
        self.traits['color'] = color
    
    def __contains__(self, key):
        return key in self.traits
    
    def __getitem__(self, key):
        return self.traits[key]

    def __setitem__(self, key, value):
        self.traits[key] = value
        
    def __delitem__(self, key):
        del self.traits[key]

    def flag(self, key):
        ''' Checking for flags - if piece dictionary doesn't
            have the key or its value is set to false,
            flag is not set.
        '''
        return key in self.traits and self.traits[key]
        
    def unset(self, flag):
        self.traits[flag] = False

    def _get_blocking(self):
        return self['blocking']
    blocking = property(_get_blocking)
    
    def _get_blocks_sight(self):
        return self['blocks sight']
    blocks_sight = property(_get_blocks_sight)
    
    def _get_shape(self):
        return self.traits['shape']
    def _set_shape(self, value):
        self.traits['shape'] = value
    shape = property(_get_shape, _set_shape)
    
    def _get_name(self):
        return self.traits['name']
    def _set_name(self, value):
        self.traits['name'] = value
    name = property(_get_name, _set_name)
    
    def _get_color(self):
        return self.traits['color']
    def _set_color(self, value):
        self.traits['color'] = value
    color = property(_get_color, _set_color)

    def move_to(self, x, y):
        self.leave()
        self._arrive_on(game.board[x, y])

    def __str__(self):
        return str(self.traits.get('name',"NoNamePiece"))
