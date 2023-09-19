'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.game_data import game
import guts.grammar as grammar
from guts.game_description import describe_item
#from guts.geometry import Point, Line, distance

class Board(object):

    def __getitem__(self,pos):
        x,y = pos
        return self._tiles[x][y]

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._tiles = [[ Tile((x,y)) 
            for y in range(self.height) ]
                for x in range(self.width) ]
    
    def _get_tiles(self):
        tiles = []
        for tile_array in self._tiles:
            tiles.extend(tile_array)
        return tiles
    tiles = property(_get_tiles)

    def cone(self, x, y, dx, dy, length):
        assert length >= 0
        orthogonal = (dx * dy == 0)
        cone_tiles = []
        for i in range(length):
            for j in range(-i, i + 1):
                xx = x + i * dx 
                xx += j * abs(dy) if orthogonal else min(j,0) * dx
                yy = y + i * dy 
                yy += j * abs(dx) if orthogonal else max(j,0) * dy * (-1) 
                if 0 <= xx < self.width and 0 <= yy < self.height:
                    cone_tiles.append(self[xx, yy])
        return cone_tiles
    
    #def spray(self, ):

    def circle(self, x, y, radius = 0):
        """ A circle in Chebyshev's metric."""
        assert radius >= 0
        return self.area(x,y,radius,radius,radius,radius)
        
    def ring(self, x, y, radius = 1, inner_radius = None):
        if inner_radius is None:
            inner_radius = radius - 1
        assert radius >= 0 and inner_radius >= 0
        return self.area(x,y,radius,radius,radius,radius, self.circle(x,y, inner_radius))
    
    def rectangle(self, x, y, width, height, filled = False):
        return self.area(x, y, 0, width, 0, height, [] if filled else self.area(x+1,y+1, 0, width - 2, 0, height - 2))
    
    def area(self, x, y, left = 0, right = 0, top = 0, bottom = 0, excluded = []):
        left = left if x - left >= 0 else x
        right = right if x + right < self.width else self.width - x - 1 
        top = top if y - top >= 0 else y
        bottom = bottom if y + bottom < self.height else self.height - y - 1  
        tiles = [] 
        for xx in range(x - left, x + right + 1):
            for yy in range(y - top, y + bottom + 1):
                tiles.append(self[xx,yy])
        for excluded_tile in excluded:
            if excluded_tile in tiles:
                tiles.remove(excluded_tile)
        return tiles
    
    def size(self):
        return (self.width, self.height)

    def contains_position(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
    
    def adjust_to_bounds(self, x, y):
        return (min(max(0,x), self.width - 1) , min(max(0,y), self.height - 1)) 

class Tile(object):
    """ This class represents one tile of a board.
    
        A tile may contain:
        * terrain - this is probably mandatory, basic element of a board
                    tile, to give shape to empty tiles. Walls, floor,
                    water, grass etc.
        * items - items that can be found on the tile. 
        * occupant - an agent that currently occupies the tile,
                    e.g. player character.
        * feature - any other thing that can occupy or be on a tile,
                    but is not an agent nor item and it doesn't qualify
                    as terrain either. E.g. trees, boulders, large computers.
                    
        The tile also knows its position on the board to let the game pieces put on it
        know where they are, 
        ***ATTENTION*** however it does not remove that knowledge once they leave.
        TODO: Should it? On one hand, maybe things could carry the knowledge with them
        in case they get temporarily off the board altogether to return later...
        but on the other hand, the effect that took them off the board could remember
        that.
    """
    
    def __init__(self, position):
        self.terrain = None
        self.feature = None
        self._occupant = None
        self.items = []
        self.explored = False
        self._visible = False
        self._remembered_shape = None
        #for debugging
        self.x, self.y = self._position = position
        
    def _get_occupant(self):
        return self._occupant
    def _set_occupant(self, occupant):
        self._occupant = occupant
        if occupant is not None:
            occupant.x, occupant.y = self._position
    occupant = property(_get_occupant, _set_occupant)

    def _get_feature(self):
        return self._feature
    def _set_feature(self, feature):
        self._feature = feature
        if feature is not None:
            feature.x, feature.y = self._position
    feature = property(_get_feature, _set_feature)

    def _get_visible(self):
        return self._visible
    def _set_visible(self, value):
        if value:
            self.explored = value
        elif self.explored:
            self._remembered_shape = self.shape
        self._visible = value
    visible = property(_get_visible, _set_visible)

    def explore(self, terrain = True, features = True, items = False, occupants = False):
        if not any([terrain, features, items, occupants]):
            self.explored = False
            self._remembered_shape = None
        elif terrain:
            self.explored = True
            self._remembered_shape = self._main_piece(occupants, features, items)
        else:
            if occupants and self.occupant is not None:
                self._remebered_shape = self.occupant.shape
                self.explored = True
            elif features and self.feature is not None:
                self._remembered_shape = self.feature.shape
                self.explored = True
            elif items and self.items: 
                self._remembered_shape = self.items[0].shape
                self.explored = True
   
    def _get_blocking_piece(self):
        if self.terrain.blocking:
            return self.terrain
        if self.feature is not None and self.feature.blocking:
            return self.feature
        if self.occupant is not None and self.occupant.blocking:
            return self.occupant
        return None
    blocking_piece = property(_get_blocking_piece)

    def is_blocked(self):
        return self.blocking_piece is not None
    
    def _blocks_sight(self):
        if self.terrain.blocks_sight:
            return True
        if self.feature is not None and self.feature.blocks_sight:
                return True
        if self.occupant is not None:
            return self.occupant.blocks_sight
        return False
    blocks_sight = property(_blocks_sight)
 
    def _get_shape(self):
        main_piece = self._main_piece()
        if self.visible:
            return main_piece.shape
        elif self.explored:
            return self._remembered_shape
        else:
            return 'nothing'
    shape = property(_get_shape)

    def _get_color(self):
        main_piece = self._main_piece()
        if self.visible:
            return main_piece.color
        else:
            return 'out of sight'
    color = property(_get_color)

    def _get_highlight(self):
        if self.occupant is None and self.items and self.feature is not None:
            return 'light gray'
        return 'black'
    highlight = property(_get_highlight)

    def _main_piece(self, include_occupant = True, include_feature = True, include_items = True):
        if self.occupant is not None and include_occupant:
            return self.occupant
        if self.feature is not None and include_feature:
            return self.feature
        if self.items and include_items:
            return self.items[0]
        return self.terrain

    def _get_pieces(self):
        return [piece for piece in [self.occupant, self.feature, self.terrain] + self.items if piece is not None]
    pieces = property(_get_pieces)
    
    def __str__(self):
        return "{0}{1}{2}{3}.".format(grammar.capitalise(self.occupant.name) + '. ' if self.occupant is not None else '', \
                                     grammar.capitalise(grammar.articled(self.feature.name)) + '. ' if self.feature is not None else '', \
                                     '' if self.items == [] else grammar.capitalise(', '.join([describe_item(item) for item in self.items])) + '. ' , \
                                     grammar.capitalise(self.terrain.name)) 
    
    def __repr__(self):
        return "%s at " % (self.__class__) + ', '.join([str(self.x),str(self.y),str(self.terrain),str(self.occupant),str(self.feature),str(self.items)])
    
    def put(self, item):
        self.items.insert(0, item)
        item.x, item.y = self._position
    
    def remove(self, item):
        self.items.remove(item)
