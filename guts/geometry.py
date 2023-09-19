'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from tcod import libtcodpy as libtcod
from .game_data import game

def distance(piece_from, piece_to):
    return _distance(piece_from.x, piece_from.y, piece_to.x, piece_to.y)

def _distance(x_from, y_from, x_to, y_to):
    """ Chebyshev metric """
    return max(abs(x_from - x_to), abs(y_from - y_to))

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __str__(self):
        return "Point at ({0}, {1})".format(self.x, self.y)

class Line(object):
    
    def __init__(self, point_from, point_to):
        from_x, from_y, to_x, to_y = point_from.x, point_from.y, point_to.x, point_to.y
        self.points = []
        self._blocking_point = None
        self._sight_blocking_point = None
 #       print(str((from_x, from_y)),str((to_x, to_y)))
        for x,y in libtcod.line_iter(from_x, from_y, to_x, to_y):
            self.points.append(Point(x,y))
            if not self.is_blocked() and game.board[x,y].is_blocked() and \
                    (x not in [from_x, to_x] or y not in [from_y, to_y]):
                self._blocking_point = Point(x,y)
            if not self.is_sight_blocked() and game.board[x,y].blocks_sight and \
                    (x not in [from_x, to_x] or y not in [from_y, to_y]):
                self._sight_blocking_point = Point(x,y)    
#        print(str(self.points))
        
    def is_blocked(self):
        return self._blocking_point is not None
    
    def _get_blocking_point(self):
        return self._blocking_point
    blocking_point = property(_get_blocking_point)
        
    def is_sight_blocked(self):
        return self._sight_blocking_point is not None
        
    def length(self):
        return distance(self.point[0], self.points[-1])
        
    def __str__(self):
        return 'Line from {0} to {1}, blocked at {2}, sight blocked at {3}, points: {4}' \
            .format(self.points[0],self.points[-1],self._blocking_point, self._sight_blocking_point, self.points) 
        
