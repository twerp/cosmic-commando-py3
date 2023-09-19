'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

import shelve
from tcod import libtcodpy as libtcod
from guts.config import GameSettings
from collections import defaultdict

class GameData(object):
    """ Game data stores all the data that is generated for the actual game.
        Part of the data is primary - that is, it is generated procedurally 
        at the beginning of the game or by player's choice or actions and
        therefore needs to be stored in a file when saving a game.
        Then, there's secondary data, that can be regenerated from the primary
        data, by simple operations (done here) or using external methods 
        - the latter data must be passed to the object of this class 
        as parameters to ensure that this module is the root dependency
        of the project.
        
    """  
    
    def __init__(self):
        """ Saving and loading data needs to make sure it doesn't store
            any object twice independently (e.g. player as a piece on 
            the board and then self.player handle), because shelve will
            NOT keep these connected. However, some pieces of the data
            might be annoying to recreate procedurally, so we can index
            them for ease of use.  
        """
        self.new()
        
    def new(self, time_limit = False):
        #Primary data:
        self._board = None
        self.msgs = []
        self.msg_archive = []
        self.quests = []
        self.kill_list = defaultdict(int)
        self.time_limited_turns = False
        self.turncount = 0
        self.state = None
        self.previous_state = None
        self.graphical_effects = []
        self.choices = {}
        self._time_limit = time_limit
        self.overlays = {} #TODO: rethink the approach to map overlays
        #Secondary data - for storing and loading via index
        self.player = None
        self._current_quest = None
        #Secondary data - for procedural recreation
        self.fov_recompute = None
        self.fov_map = None
        #fleeting data - no need to store it
        self._infotips = []
        self._infotips_viewed = False 

    def is_time_limited(self):
        return self._time_limit
           
    def remove_time_limit(self):
        self._time_limit = False
           
    def gfx(self, x, y, color):
        self.graphical_effects.append((x,y, color))
        if self.state != 'show gfx':
            self.previous_state = self.state
        self.state = 'show gfx'    
    
    def note_death(self, victim):
        self.kill_list[victim['name']] += 1
    
    def _get_current_quest(self):
        return self._current_quest
    
    def _set_current_quest(self, value):
        value.status = 'current'
        self._current_quest = value
    
    current_quest = property(_get_current_quest,_set_current_quest)
    
    def add_infotip(self, infotip, color):
        if self._infotips_viewed:
            self._infotips = []
            self._infotips_viewed = False
        self._infotips.append((infotip, color))
    
    def _get_infotips(self):
        self._infotips_viewed = True
        return self._infotips
    infotips = property(_get_infotips)
        
    def _get_pieces(self):
        pieces = []
        for tile in self.board.tiles:
            pieces.extend(tile.pieces)
        return pieces
    pieces = property(_get_pieces)
    
    def _get_agents(self):
        agents = []
        for tile in self.board.tiles:
            if tile.occupant is not None:
                agents.append(tile.occupant)
        return agents
    agents = property(_get_agents)
    
    def _get_board(self):
        return self._board
    def _set_board(self, board):
        self.fov_recompute = None
        self.fov_map = None
        self._pieces = None
        self._agents = None
        self._board = board
    board = property(_get_board, _set_board)
    
    def initialize_vision(self):
        self.fov_recompute = True
        game.fov_map = libtcod.map_new(self.board.width, self.board.height)
        for y in range(self.board.height):
            for x in range(self.board.width):
                game._set_fov_at(x, y)
    
    def _set_fov_at(self, x, y):
        libtcod.map_set_properties(self.fov_map, x, y, not self.board[x,y].blocks_sight, not self.board[x,y].is_blocked)
      
    def is_visible(self, piece):
        return game.board[piece.x, piece.y].visible if game.state.find('briefing') < 0 else False
    
    def _get_tiles_in_fov(self):
        return [tile for tile in self.board.tiles if tile.visible]
    tiles_in_sight = property(_get_tiles_in_fov)
    
    def _get_agents_in_fov(self):
        agents = []
        for tile in self.tiles_in_sight:
            if tile.occupant is not None:
                agents.append(tile.occupant)
        return agents
    agents_in_sight = property(_get_agents_in_fov)

    def change_visibility_at(self, x,y):
        game.fov_recompute = True
        game._set_fov_at(x,y)
    
    def fov_check(self):
        #recompute FOV if needed (the player moved or something)
        if self.fov_recompute:
            libtcod.map_compute_fov(self.fov_map, self.player.x, self.player.y, self.player['sight'], GameSettings.FOV_LIGHT_WALLS, GameSettings.FOV_ALGO)
            self.fov_recompute = False
            return True
        return False
        
    def save(self, savegame):
        """ If the same object is shelved two times (e.g. by itself and as a part of
            a collection, weird things happen. Make sure it doesn't happen.
        """
        #open a new empty shelve (possibly overwriting an old one) to write the game data
        savefile = shelve.open(savegame, 'n')
        #primary data
        savefile['board'] = self.board
        savefile['quests'] = self.quests
        savefile['messages'] = self.msgs
        savefile['message archive'] = self.msg_archive
        savefile['game state'] = self.state
        savefile['game previous state'] = self.previous_state
        savefile['time limited turns'] = self.time_limited_turns
        savefile['turncount'] = self.turncount
        savefile['kill list'] = self.kill_list
        savefile['graphical effects'] = self.graphical_effects
        savefile['choices'] = self.choices
        savefile['time limited mode'] = self._time_limit
        savefile['overlays'] = self.overlays
        #secondary data 
        if self.current_quest is not None:
            savefile['current quest'] = self.current_quest.name
        savefile['player position'] = (self.player.x, self.player.y)
        savefile['player'] = self.player #between visiting maps, the player might exist while the board doesn't, this handles such cases
        savefile.close()
        
    def load(self, savegame):
        self.new()
        #open the previously saved shelve and load the game data
        savefile = shelve.open(savegame, 'r')
        #primary data
        self.board = savefile['board'] 
        self.quests = savefile['quests']
        self.msgs = savefile['messages'] 
        self.msg_archive = savefile['message archive'] 
        self.state = savefile['game state']
        self.previous_state = savefile['game previous state'] 
        self.time_limited_turns = savefile['time limited turns']
        self.turncount = savefile['turncount']
        self.kill_list = savefile['kill list']
        self.graphical_effects = savefile['graphical effects']
        self.choices = savefile['choices']  
        self._time_limit = savefile['time limited mode']
        self.overlays = savefile['overlays']
        #secondary data
        self._current_quest = [quest for quest in self.quests if quest.name == savefile['current quest']][0] if 'current quest' in savefile else None
        self.player = savefile['player']
        if self.board is not None: 
            player_x, player_y = savefile['player position']
            game.board[player_x, player_y].occupant = self.player 
        savefile.close()
        self.prepare_secondary_data()
    
    def prepare_secondary_data(self):
        #TODO: regenerate
        pass 

game = GameData()
