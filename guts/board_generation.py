'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from .game_pieces import *
from .game_tileboard import *
from tcod import libtcodpy as libtcod
from .utils import *
from guts.game_piece_defs import *
from guts.game_quests import Objective
from guts.debug import debug
from guts.game_data import game
from guts.geometry import Line, distance, Point

class Rect(object):
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.x_end = x + width + 1
        self.y_end = y + height + 1
        self.w = width
        self.h = height
    
    def center(self):
        center_x = (self.x + self.x_end) / 2
        center_y = (self.y + self.y_end) / 2
        return (center_x, center_y)
 
    def covers(self, x, y):
        return (x >= self.x and x < self.x_end) and (y >= self.y and y < self.y_end)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x  < other.x_end and self.x_end > other.x and
                self.y  < other.y_end and self.y_end > other.y)

    def __repr__(self):
        return str(self.__class__) + str((self.x,self.y,self.x_end,self.y_end))

def generate_board(width, height, player, mission):
    generator = BoardGenerator(mission, width, height)
    generator.generate()
    generator.place_player(player)
    return generator.board

class BoardGenerator(object):
    
    def __init__(self, mission, board_width, board_height):
        self.board = Board(board_width, board_height)
        self.mission = mission
        self.rooms = []
        self.default_floor = 'floor'
        self.vault_positioner_data = None
    
    def generate(self):
        if self.mission == 'Huginn':
            self.create_huginn()
        elif self.mission.find('Aster') >= 0:
            self.create_zero_gravity_level()
        elif self.mission.find('Test') >= 0:
            self.create_test_chamber()
        elif self.mission.find('Murder') >= 0:
            self.build_nightmarish_board()
            self.populate_nightmarish_board()
        else:
            self.max_rooms = 25
            self.room_min_size = 3
            self.room_max_size = 10
            self.build_board()
            self.populate_board()
    
    def spawn_posse(self, x, y, posse_member_type, posse_number, posse_member_name = None):
        acceptable_directions = []
        for direction in compass_directions:
            dx, dy = directions[direction]
            if not self.board[x + dx, y + dy].is_blocked():
                acceptable_directions.append(direction)
        bodyguard_spawns = random_combination(acceptable_directions, min(len(acceptable_directions), posse_number))
        for spawn_point in bodyguard_spawns:
            dx, dy = directions[spawn_point]
            self.board[x + dx, y + dy].occupant = new_agent(posse_member_type, posse_member_name)

    def put_doors_in(self, room):
        for x in range(room.x, room.x_end):
            if not self.board[x, room.y].is_blocked():
                self.board[x, room.y].feature = new_feature('closed door')
            if not self.board[x, room.y_end].is_blocked():
                self.board[x, room.y_end].feature = new_feature('closed door')
        for y in range(room.y, room.y_end):
            if not self.board[room.x, y].is_blocked():
                self.board[room.x, y].feature = new_feature('closed door')
            if not self.board[room.x_end, y].is_blocked():
                self.board[room.x_end, y].feature = new_feature('closed door')
    
    def create_zero_gravity_level(self):
        def generate_asteroid(x0,y0,w,h,volume):
            assert volume < w*h
            center_point = (random_pos(w) + x0, random_pos(h) + y0)
            asteroid = set([center_point])
            x,y = center_point
            while len(asteroid) < volume:
                if coinflip():
                    dx, dy = directions[random_choice(cardinal_directions)]
                    x,y = x + dx, y + dy
                    x = x0 if x < x0 else x0 + w if x >= x0 + w else x
                    y = y0 if y < y0 else y0 + h if y >= y0 + h else y
                    asteroid.add((x,y))
                else:
                    if x != center_point[0]:
                        x -= 1 if x > center_point[0] else -1
                    if y != center_point[1]:
                        y -= 1 if y > center_point[1] else -1
            return asteroid
        def populate_asteroid_field(x0,y0,xE,yE,density):
            #TODO: generalize
            asteroids = []
            for _ in range(density):
                    vol = random_int(5,20)
                    new_asteroid = generate_asteroid(x0,y0,xE-x0,yE-y0,vol)
                    ok = True
                    for asteroid in asteroids:
                        if asteroid.intersection(new_asteroid):
                            ok = False
                            break
                    if ok:
                        asteroids.append(new_asteroid)
            return asteroids
        def create_emptiness(x0,y0, xE,yE):
            for x in range(x0, xE + 1):
                for y in range(y0, yE + 1):
                    self.board[x,y].feature = None
        def create_spaceship(x0,y0, shape, feature):
            neighbours = []
            for y in range(len(shape)):
                shape_row = shape[y] 
                for x in range(len(shape_row)):
                    self.board[x0+x,y0+y].feature = new_feature(feature) if shape_row[x] == 1 else None
                    neighbours.append((x0 + x - 1, y0 + y))
            return neighbours
        def compute_trajectory(x0,y0,target_fields):
            abc_map=libtcod.map_new(self.board.width - 2,self.board.height - 2)
            libtcod.map_clear(abc_map, True, True)
            for x in range(1, self.board.width):
                for y in range(1, self.board.height):
                    if self.board[x,y].is_blocked():
                        libtcod.map_set_properties(abc_map,x-1,y-1,False, False)
            path = None
            for xE, yE in random_permutation(target_fields):
                path = libtcod.path_new_using_map(abc_map, 1.0)
                if libtcod.path_compute(path, x0, y0, xE, yE):
                    break
            trajectory = []
            initial_path_step = libtcod.path_size(path) % 3
            initial_path_step += 5 if initial_path_step == 2 else 8   
            headstart_x, headstart_y = libtcod.path_get(path, initial_path_step)
            for _ in range(initial_path_step + 1):
                libtcod.path_walk(path,False)
            assert libtcod.path_size(path) % 3 == 0
            while not libtcod.path_is_empty(path) :
                x,y=libtcod.path_walk(path,False)
                if not x is None :
                    #self.board[x+1, y+1].terrain = new_terrain('holowall')
                    trajectory.append((x+1,y+1))
                else :
                    debug.log("Pathfinding fail.")
                    break
            return (headstart_x + 1, headstart_y + 1, trajectory)
        game.player['sight'] = max(int(1.5*self.board.width), int(1.5*self.board.height))
        for x in range(self.board.width):
            for y in range(self.board.height):
                if coinflip() and coinflip():
                    self.board[x,y].terrain = new_terrain('void')
                else:
                    self.board[x,y].terrain = new_terrain('starry void')
                    self.board[x,y].terrain.shape = random_choice(['starry', 'double starry', 'single starry'])
                    self.board[x,y].terrain.color = random_weighted_choice({
                        'star class O': 1, 'star class B': 2, 'star class A': 3,
                        'star class F': 4, 'star class G': 5, 'star class K': 6,'star class M': 7,
                                 })
        airlock = random_int(self.board.height//2 - 4,self.board.height//2 + 4)
        self.rooms.append(Rect(1,airlock, 1,airlock))
        for asteroid in populate_asteroid_field(6,0,self.board.width - 5, self.board.height - 1,150):
            for x,y in asteroid:
                self.board[x,y].feature = new_feature('asteroid')
        #create_emptiness(1,self.board.height/2 - 5, 2,self.board.height/2 + 5)
        #create_spaceship(1,self.board.height/2 - 5, 10,self.board.height/2 + 5, None)
        target_coords = create_spaceship(self.board.width - 5, random_int(5, self.board.height - 6), 
                         [[0,0,0,0,1],[0,0,0,1,1],[0,0,1,1,1],[0,1,1,1,1],[1,1,0,1,1]], 'Blue Crow')
        for y in range(self.board.height//2 - 5, self.board.height//2 + 6):
            self.board[0,y].feature = new_feature('spaceship hull')
        headstart_x, headstart_y, trajectory = compute_trajectory(1, airlock, target_coords)
        self.board[headstart_x, headstart_y].occupant = new_agent('Space Pirate Captain Bluesteel')
        self.board[headstart_x, headstart_y].occupant['trajectory'] = trajectory
                
    def create_test_chamber(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                self.board[x,y].terrain = new_terrain('lab wall')
        self.default_floor = 'lab floor'
        self.create_room(Rect(0, 0, 7, 7))
        self.create_room(Rect(8, 0, 7, 7))
        (prev_x, prev_y) = self.rooms[0].center()
        for direction in eight_directions:
            self.board[prev_x + direction[0], prev_y + direction[1]].put(new_item('frag grenade'))
        
        (new_x, new_y) = self.rooms[1].center()
        if coinflip():
            #first move horizontally, then vertically
            self.create_h_tunnel(prev_x, new_x, prev_y)
            self.create_v_tunnel(prev_y, new_y, new_x)
        else:   
            #first move vertically, then horizontally
            self.create_v_tunnel(prev_y, new_y, prev_x)
            self.create_h_tunnel(prev_x, new_x, new_y)
        self.doors_in_rooms()
        x,y = self.rooms[1].center()
        if self.mission.find('1') >= 0: #cybork
            self.board[x,y].occupant = new_agent('cybork', name = 'Test Cybork')
            self.spawn_posse(x,y,'Raven recruit', random_nat(1)+2)
        elif self.mission.find('2') >= 0: #raven officer + posse
            self.board[x,y].occupant = new_agent('Raven officer')
            self.spawn_posse(x,y,'Raven recruit', random_nat(1)+2)
        elif self.mission.find('Final') >= 0:
            self.board[prev_x + 2, prev_y].occupant = new_agent('Raven scientist', name = 'Raven doorman')
            self.board[x,y].occupant = new_agent('Raven general')
            self.spawn_posse(x,y,'Raven officer', random_nat(1)+3, 'Raven bodyguard')
            for quest in game.quests:
                if not quest.is_finished():
                    if quest.name in ['Huginn','Test 1']:
                        self.spawn_posse(x,y,'cybork', 1)
                    else:
                        self.spawn_posse(x,y,'Raven officer', 1)
                        self.spawn_posse(x,y,'Raven recruit', random_nat(1)+2)
                pass
        else:
            debug.log("Unknown Test Chamber.")
        
        
    def create_room(self, room, terrain = None):
        if terrain is None:
            terrain = self.default_floor
        #go through the tiles in the rectangle and make them passable
        for x in range(room.x + 1, room.x_end):
            for y in range(room.y + 1, room.y_end):
                self.board[x,y].terrain = new_terrain(terrain)
        self.rooms.append(room)
        return room

    def create_h_tunnel(self, x1, x2, y, terrain = None):
        if terrain is None:
            terrain = self.default_floor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.board[x,y].terrain = new_terrain(terrain)

    def create_v_tunnel(self, y1, y2, x, terrain = None):
        if terrain is None:
            terrain = self.default_floor
        #vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.board[x,y].terrain = new_terrain(terrain)

    def vault_position(self, width_offset, length_offset):
        x, y, x_sign, y_sign, offset_sign, side = self.vault_positioner_data
        x_result = x + width_offset * offset_sign if side in ['N', 'S'] else x + length_offset * x_sign
        y_result = y + width_offset * offset_sign if side in ['E', 'W'] else y + length_offset * y_sign
        return (x_result,y_result)
    
    def prepare_boss_room(self, side, room_width, room_length, floor, wall):
        room_x_size = room_length if side in ['W','E'] else room_width
        room_y_size = room_length if side in ['N','S'] else room_width
        if side in ['E', 'W']:
            room_x = self.board.width - 3 if side == 'W' else 2 
            room_y = random_int(2, self.board.height - 3 - room_y_size)
        else:
            room_x = random_int(2, self.board.width - 3 - room_x_size)
            room_y = self.board.height - 3 if side == 'N' else 2 
        x_sign = 1 if side == 'W' else -1
        y_sign = 1 if side == 'N' else -1
        room = Rect(room_x - room_x_size if side == 'W' else room_x, room_y - room_y_size if side == 'N' else room_y, room_x_size, room_y_size)
        for tile in self.board.rectangle(room.x, room.y, room_x_size, room_y_size):
            tile.terrain = new_terrain(wall)
        for tile in self.board.rectangle(room.x + 1, room.y + 1, room_x_size - 2, room_y_size - 2, filled = True):
            tile.terrain = new_terrain(floor)
        return room, x_sign, y_sign, room_x_size, room_y_size

    def create_pipers_cave(self, side):
        room_width = 4
        room_length = 8
        room, x_sign, y_sign, room_x_size, room_y_size = self.prepare_boss_room(side, room_width, room_length,
                         floor = 'dirt', wall = 'slag heap of trash')
        if random_choice(['left', 'right']) == 'left':
            begin_x = room.x # only one of begin_x, begin_y will be used depending on side
            begin_y = room.y
            offset_sign = 1
        else:
            begin_x = room.x_end - 1
            begin_y = room.y_end - 1
            offset_sign = -1
        if side in ['E', 'W']:
            self.vault_positioner_data = (room.x if side == 'W' else room.x + room_x_size, begin_y, x_sign, y_sign, offset_sign, side)
        else: # side in [N, S]:
            self.vault_positioner_data = (begin_x, room.y if side == 'N' else room.y + room_y_size, x_sign, y_sign, offset_sign, side)
        for i in range(3):
            x, y = self.vault_position(2, 2 * (i+1))
            self.board[x,y].occupant = new_agent(random_choice(['rabid ratling', 'ratling scavenger', 'ratling warrior', 'rat hound']))
            x, y = self.vault_position(2 + (-1)**i, 2 * (i+1))
            self.board[x,y].feature = new_feature('pile of trash')
        x, y = self.vault_position(2, 0)
        self.board[x,y].terrain = new_terrain('dirt')
        self.board[x,y].feature = new_feature('wooden door')
        x, y = self.vault_position(2 + (-1)**i,7)
        self.board[x,y].occupant = new_agent('the Piper')
        x, y = self.vault_position(2 + (-1)**(i+1),7)
        self.board[x,y].feature = new_feature('filthy mattress')
        message("You begin your extermination of vermin in the Rat-infested Landfill!", "Rat-infested Landfill")
        return room

    def spawn_furniture(self, room, furniture_type, name = None):
        #TODO: only corners for now
        x = 1 if coinflip() else room.w - 1
        y = 1 if coinflip() else room.h - 1
        self.board[x + room.x,y + room.y].feature = new_feature(furniture_type, name = name)

    def create_huginn(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                self.board[x,y].terrain = new_terrain('lab wall')
        self.default_floor = 'lab floor'
        #TODO: randomize once it works
        lab_w = self.board.width - 1
        lab_h = self.board.height - 1
        #lab_w = int(0.9 * self.board.width) + random_nat(int(0.1 * self.board.width))
        #lab_h = int(0.9 * self.board.height) + random_nat(int(0.1 * self.board.height))
        lab_room_count = 0
        #outer_entrance = coinflip()
        outer_entrance = True
        #entrance_side = random_choice(cardinal_directions)
        entrance_side = 'W'
        margin = 5
        lab_x = margin if outer_entrance and entrance_side == "W" else 0
        lab_y = margin if outer_entrance and entrance_side == "N" else 0
        if outer_entrance and entrance_side == "E":
            lab_w -= margin
        if outer_entrance and entrance_side == "S":
            lab_h -= margin
        corridor_size = random_int(2,4)
        outer_room_diameter = {'N' : random_int(5, 8), 'S' : random_int(5, 8), 'E' : random_int(5, 8), 'W' : random_int(5, 8)}
        #create entrance
        if outer_entrance:
            #entry_x = 0 if entrance_side == "W" else lab_w - outer_room_diameter['E'] if entrance_side == "E" else random_int(outer_room_diameter['W'], lab_w - outer_room_diameter['E'] - corridor_size) 
            #entry_y = 0 if entrance_side == "N" else lab_h - outer_room_diameter['S'] if entrance_side == "S" else random_int(outer_room_diameter['N'], lab_h - outer_room_diameter['S'] - corridor_size)
            #TODO: randomize
            entry_x = 0 if entrance_side == "W" else lab_w - outer_room_diameter['E'] - 2 if entrance_side == "E" else outer_room_diameter['W'] + 2 
            entry_y = 0 if entrance_side == "N" else lab_h - outer_room_diameter['S'] - 2 if entrance_side == "S" else outer_room_diameter['N'] + 2
            entry_w = margin + outer_room_diameter[entrance_side] + 2 if entrance_side in ["E", "W"] else corridor_size
            entry_h = corridor_size if entrance_side in ["E", "W"] else margin  + outer_room_diameter[entrance_side] + 2
            entry_room = Rect(entry_x, entry_y, entry_w, entry_h)
            self.create_room(entry_room)
            for i in range(corridor_size):
                self.board[entry_x, entry_y + i + 1].feature = new_feature('closed door', 'exit')             
                self.board[entry_room.x_end - 1, entry_y + i + 1].feature = new_feature('closed door', 'lab door')
            self.board[entry_room.x_end - 2, entry_y + 1].occupant = new_agent('Raven security guard')
            self.board[entry_room.x_end - 2, entry_room.y_end - 1].occupant = new_agent('Raven security guard')
        else:
            pass
        
        def create_door(room, direction):
            door_x, door_y = room.x, room.y
            if direction in ['N', 'S']:
                door_x += random_pos(room.w - 1)
            elif direction == 'E':
                door_x = room.x_end
            if direction in ['E', 'W']:
                door_y += random_pos(room.h - 1)
            elif direction == 'S':
                door_y = room.y_end
            self.board[door_x, door_y].terrain = new_terrain('lab floor')
            self.board[door_x, door_y].feature = new_feature('closed door', 'lab door')             

        def spawn_opponents(room, agent_type, number):
            i, failover = 0, 100
            while i < number and failover > 0:
                x, y = room.x + random_pos(room.w - 1), room.y + random_pos(room.h - 1) 
                if not self.board[x, y].is_blocked():
                    self.board[x, y].occupant = new_agent(agent_type)
                    i += 1
                failover -= 1

        def spawn_guards(room, agent_type):
            wide_spawn = room.w >= room.h
            x, y = room.x, room.y
            s = game.player['sight']
            while True:
                x = x + random_int(s/2, s) if wide_spawn else room.x + random_pos(room.w)
                y = room.y + random_pos(room.h) if wide_spawn else y + random_int(s/2, s)
                self.board[x,y].occupant = new_agent(agent_type)
                break_value = room.x_end - x if wide_spawn else room.y_end - y
                if break_value <= s:
                    break  

        #TODO: account for inner entrance
        #create and populate corridors
        #TODO: account for inner entrance (inner_room_diameter)
        corridor_x = (lab_x + outer_room_diameter['W'] + 2, lab_w - outer_room_diameter['E'] - 2)
        corridor_w = corridor_x[1] - corridor_x[0]
        corridor_y = (lab_y + outer_room_diameter['N'] + 2, lab_h - outer_room_diameter['S'] - 2)
        corridor_h = corridor_y[1] - corridor_y[0]
        self.create_room(Rect(corridor_x[0], corridor_y[0], corridor_w, corridor_size))
        spawn_guards(self.rooms[-1], 'Raven security guard')
        spawn_opponents(self.rooms[-1], 'Raven scientist', random_pos(2))
        self.create_room(Rect(corridor_x[0], corridor_y[0], corridor_size, corridor_h))
        spawn_guards(self.rooms[-1], 'Raven security guard')
        spawn_opponents(self.rooms[-1], 'Raven scientist', random_pos(2))
        self.create_room(Rect(corridor_x[1] - corridor_size, corridor_y[0], corridor_size, corridor_h))
        spawn_guards(self.rooms[-1], 'Raven security guard')
        spawn_opponents(self.rooms[-1], 'Raven scientist', random_pos(2))
        self.create_room(Rect(corridor_x[0], corridor_y[1] - corridor_size, corridor_w, corridor_size))
        spawn_guards(self.rooms[-1], 'Raven security guard')
        spawn_opponents(self.rooms[-1], 'Raven scientist', random_pos(2))
        

        #TODO:  enemies        
        #create and populate outer rooms
        outer_room_x = (corridor_x[0] - outer_room_diameter['W'] - 1, corridor_x[1] + 1)
        outer_room_y = (corridor_y[0] - outer_room_diameter['N'] - 1, corridor_y[1] + 1)
        outer_room_w = corridor_w
        outer_room_h = corridor_h
        #TODO: account for dynamic entrance
        def outer_rooms(room_start, room_const, vertical, room_size, room_space, door_side):
            var = room_start
            lab_room_count = 0
            while room_space > var - room_start:
                size = min(random_choice([3,3,4,5]), room_space + room_start - var + 1)
                r_x = room_const if vertical else var
                r_y = var if vertical else room_const
                r_w = room_size if vertical else size
                r_h = size if vertical else room_size
                if size <= 3: #subject- cybork room
                    r_floor = 'slime-covered floor'
                    agent_type = 'cybork'
                    agent_number = 1
                else: # research room
                    r_floor = 'lab floor'
                    agent_type = 'Raven scientist'
                    lab_room_count += 1
                    agent_number = random_pos(size*room_size/6)
                new_room = self.create_room(Rect(r_x, r_y, r_w, r_h), r_floor)
                create_door(new_room, door_side)
                if size > 3: # lab room
                    self.spawn_furniture(new_room, 'lab workstation')
                spawn_opponents(new_room, agent_type, agent_number)
                var += size
                if vertical:
                    self.create_h_tunnel(room_const, room_const + room_size, var, 'lab wall')
                else: 
                    self.create_v_tunnel(room_const, room_const + room_size, var, 'lab wall')
                #var += 1
            return lab_room_count
        """
        north_rooms = self.create_room(Rect(outer_room_x[0], outer_room_y[0], outer_room_w + outer_room_diameter['W'] + 2, outer_room_diameter['N']))
        west_rooms = self.create_room(Rect(outer_room_x[0], entry_y + corridor_size + 1, outer_room_diameter['W'] , outer_room_h -  corridor_size))
        south_rooms = self.create_room(Rect(corridor_x[0], outer_room_y[1], outer_room_w, outer_room_diameter['S']))
        east_rooms = self.create_room(Rect(outer_room_x[1], corridor_y[0], outer_room_diameter['E'], outer_room_h))
        """
        north_rooms = Rect(outer_room_x[0], outer_room_y[0], outer_room_w + outer_room_diameter['W'] + 2, outer_room_diameter['N'])
        west_rooms = Rect(outer_room_x[0], entry_y + corridor_size + 1, outer_room_diameter['W'] , outer_room_h -  corridor_size)
        south_rooms = Rect(corridor_x[0], outer_room_y[1], outer_room_w, outer_room_diameter['S'])
        east_rooms =  Rect(outer_room_x[1], corridor_y[0], outer_room_diameter['E'], outer_room_h)
        
        lab_room_count += outer_rooms(north_rooms.x, north_rooms.y, False, outer_room_diameter['N'], north_rooms.w, 'S')
        lab_room_count += outer_rooms(south_rooms.x, south_rooms.y, False, outer_room_diameter['S'], south_rooms.w, 'N')
        lab_room_count += outer_rooms(west_rooms.y, west_rooms.x, True, outer_room_diameter['W'], west_rooms.h, 'E')
        lab_room_count += outer_rooms(east_rooms.y, east_rooms.x, True, outer_room_diameter['E'], east_rooms.h, 'W')

        #create and populate inner rooms
        inner_x  = corridor_x[0] + corridor_size + 1
        inner_y = corridor_y[0] + corridor_size + 1
        inner_w = corridor_w - 2 * corridor_size - 2 
        inner_h = corridor_h - 2* corridor_size - 2
        
        
        def has_partition(n, min_part, max_part):
            if n >= min_part and n <= max_part:
                return True
            if n < min_part:
                return False
            for i in range(min_part, max_part + 1):
                if has_partition(n - i, min_part, max_part):
                    return True
        inner_room_y = inner_y
        while inner_room_y < inner_y + inner_h:
            room_heights = random_permutation([2,2,3,3,4])
            for inner_room_h in room_heights:
                space_left = inner_y + inner_h - inner_room_y - inner_room_h
                if space_left == 0 or has_partition(inner_y + inner_h - inner_room_y - inner_room_h,3,5):
                    break
            inner_rooms = []
            if inner_w >= 7:
                if True:
                    split_w0 = inner_w/2 + random_int(-1,1)
                    split_w1 = inner_w - split_w0 - 1
                    split_x = inner_x + split_w0 + 1  
                    type0 = type1 = 'subject' if inner_room_h == 2 else 'lab'
                else:
                    pass
                inner_rooms.append((inner_x, split_w0, type0))
                inner_rooms.append((split_x, split_w1, type1))
                
            else:
                inner_rooms.append((inner_x, inner_w, 'subject' if inner_room_h == 2 or (inner_room_h == 3 and random_pos(3) == 1) else 'lab'))
            for inner_room_x, inner_room_w, inner_room_type in inner_rooms:
                if inner_room_type == 'subject':
                    floor = 'slime-covered floor'
                    agent_type = 'cybork'
                    agent_number = 1
                else:
                    lab_room_count += 1
                    floor = 'lab floor'
                    agent_type = 'Raven scientist'
                    agent_number = random_pos(inner_room_h * inner_room_w/6)
                new_room = self.create_room(Rect(inner_room_x, inner_room_y, inner_room_w, inner_room_h), floor)
                create_door(new_room, 'W' if inner_room_x == inner_x else 'E')
                if inner_room_type == 'lab':
                    self.spawn_furniture(new_room, 'lab workstation')
                spawn_opponents(new_room, agent_type, agent_number)    
            inner_room_y += inner_room_h + 1
        game.current_quest.get_goal('lab sabotage').repeats = lab_room_count
    
    def create_spaceport(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                self.board[x,y].terrain = new_terrain('floor')
        
    def occupy_room(self, room, agent_type):
        available_tiles = []
        for tile in self.board.rectangle(room.x, room.y, room.w, room.h):
            if not tile.is_blocked():
                available_tiles.append(tile)
        if available_tiles:
            tile = random_choice(available_tiles)
            tile.occupant = new_agent(agent_type)
            return True
        else:
            return False

    def build_board(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                self.board[x,y].terrain = new_terrain('wall')
        num_rooms = 0
        for _ in range(self.max_rooms):
            #random width and height
            w = random_int(self.room_min_size, self.room_max_size)
            h = random_int(self.room_min_size, self.room_max_size)
            #random position without going out of the boundaries of the map
            x = random_int(0, self.board.width - w - 2)
            y = random_int(0, self.board.height - h - 2)
            #"Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)
            if x + w >= self.board.width or y + h >= self.board.height: 
                print((x,y,w,h))
            #run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
            if not failed:
                #this means there are no intersections, so this room is valid
                #"paint" it to the map's tiles
                self.create_room(new_room)
                #center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()
                if num_rooms != 0:
                    #all rooms after the first:
                    #connect it to the previous room with a tunnel
                    #center coordinates of previous room
                    (prev_x, prev_y) = self.rooms[num_rooms-1].center()
                    #draw a coin (random number that is either 0 or 1)
                    if coinflip():
                        #first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:   
                        #first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                #add some contents to this room, such as monsters
                num_rooms += 1    

    def doors_in_rooms(self):
        #features first
        for room in self.rooms:
            for x in range(room.x, room.x_end):
                if not self.board[x, room.y].is_blocked():
                    self.board[x, room.y].feature = new_feature('closed door')
                if not self.board[x, room.y_end].is_blocked():
                    self.board[x, room.y_end].feature = new_feature('closed door')
            for y in range(room.y, room.y_end):
                if not self.board[room.x, y].is_blocked():
                    self.board[room.x, y].feature = new_feature('closed door')
                if not self.board[room.x_end, y].is_blocked():
                    self.board[room.x_end, y].feature = new_feature('closed door')

    def build_nightmarish_board(self):
        for tile in self.board.rectangle(0,0,self.board.width -1, self.board.height -1):
            #tile.terrain = new_terrain(self.board_by_quest[self.mission]['outer wall'])
            tile.terrain = new_terrain('way off the spaceport')
        entrance_side = random_choice(cardinal_directions)


        #if not main_room.covers(x,y):
        for x in range(1, self.board.width - 1):
            for y in range(1, self.board.height - 1):
                self.board[x,y].terrain = new_terrain('spacestrip')
        """                
        for x in range(0, self.board.width):
            for y in range(0, self.board.height):
                if self.board[x,y].terrain is None:
                    print(x,y)
        """
        room_size = 1
        side_coords = {'W' : (1, self.board.width/2),
                       'N' : (self.board.width/2, 1),
                       'E' : (self.board.width - room_size - 1, self.board.width/2),
                       'S' : (self.board.width/2, self.board.height - room_size - 1)
                       }
        player_room = Rect(side_coords[entrance_side][0], side_coords[entrance_side][1], room_size, room_size)
        self.rooms = [player_room]

    def place_rectangular_feature(self, start_x, start_y, width, height, feature_type):
        """ This is not as random or good as it could be.
        """
        sides_to_try = random_permutation([(-1,-1), (-1,1), (1,-1), (1,1)])
        for side_w, side_h in sides_to_try:
            x = start_x + ((side_w - 1)/2) * width
            y = start_y + ((side_h - 1)/2) * height
            free_floor = False
            if x > 0 and x + width < self.board.width and y > 0 and y + height < self.board.height:
                free_floor = True
                xx = x
                while xx <= x + width and free_floor:
                    for yy in range(y, y + height + 1):
                        if self.board[xx,yy].is_blocked() or self.board[xx, yy].feature is not None:
                            free_floor = False
                            break
                    xx += 1
            if free_floor:
                for xx in range(x, x + width + 1):
                    for yy in range(y, y + height + 1):
                        self.board[xx,yy].feature = new_feature(feature_type)
                return True
        return False
        

    def populate_nightmarish_board(self):
        monster_population = ['Raven repairman'] * 24 + ['Raven spaceship pilot'] * 12
        
        cockpits = []
        max_cockpits = random_int(10,12)
        while len(cockpits) < max_cockpits:
            x = random_pos(self.board.width - 2)
            y = random_pos(self.board.height - 2)
            width, height = (4,2) if coinflip() else (2,4)
            if self.place_rectangular_feature(x, y, width, height, 'spaceship hull'):
                self.board[x,y].feature = new_feature('spaceship cockpit') 
                cockpits.append(Point(x,y))
        max_distance_cockpit = None
        max_distance = None
        p = Point(*self.player_position())
        for cockpit in cockpits:
            current_dist = distance(cockpit, p)
            if max_distance_cockpit is None or  current_dist > max_distance:
                max_distance_cockpit = cockpit
                max_distance = current_dist
        self.board[max_distance_cockpit.x, max_distance_cockpit.y].feature = new_feature("spaceship cockpit w/iff", name = 'spaceship cockpit')
        carts = random_int(16,20)
        while carts > 0:
            x = random_pos(self.board.width - 2)
            y = random_pos(self.board.height - 2)
            if not self.board[x,y].is_blocked():
                self.board[x,y].feature = new_feature('repair cart')
                carts -= 1
        #print(monster_population)
        monster_population = random_permutation(monster_population)
        room_density = 6
        room_width = self.board.width / room_density
        room_height = self.board.width / room_density
        rooms = [[Rect(i * room_width, j * room_height, room_width, room_height) for i in range (room_density)] for j in range(room_density)]
        for room_row in random_permutation(rooms):
            for room in random_permutation(room_row):
                #if not room.intersect(self.rooms[1]) and monster_population:
                if monster_population:
                    agent_type = monster_population.pop()
                    if not self.occupy_room(room, agent_type):
                        monster_population.append(agent_type)

    def populate_board(self):
        #enemies! we need enemies!
        for room in self.rooms:
            x,y = room.center()
            self.put_doors_in(room)
            if not self.board[x,y].is_blocked():
                if game.current_quest.name == 'Muninn':
                    self.board[x,y].occupant = new_agent('Raven officer')
                    self.spawn_posse(x, y, 'Raven recruit', random_nat(1)+2)
                elif game.current_quest.name == "Raven's Nest" :
                    if coinflip():
                        self.spawn_posse(x, y, 'cybork', random_nat(0)+2)
                    else:
                        self.board[x,y].occupant = new_agent('Raven officer')
                        self.spawn_posse(x, y, 'Raven security guard', random_nat(0)+2)
                else:
                    self.board[x,y].occupant = new_agent('cybork')
        for i in range(1,10):
            x,y = directions[i]

        first_point = Point(*self.rooms[0].center())
        rooms_by_distance = []     
        for room in self.rooms[1:]:
            p = Point(*room.center())
            rooms_by_distance.append((distance(first_point, p), room))
        last_room = sorted(rooms_by_distance, key = lambda x: x[0], reverse = True)[0][1]
        if game.current_quest.name == 'Muninn':
            self.spawn_furniture(last_room, 'data console')
        else:
            for x in range(self.rooms[0].x, self.rooms[0].x_end):
                for y in range(self.rooms[0].y, self.rooms[0].y_end):
                    self.board[x,y].occupant = None
            for x in range(room.x, room.x_end):
                for y in range(room.y, room.y_end):
                    self.board[x,y].occupant = None
            x,y = last_room.center()
            self.board[x,y].occupant = new_agent("Lady Raven")
            self.spawn_posse(x, y, "Corvid-class Mech", 8)
        
    def player_position(self):
        first_room = self.rooms[0]
        return first_room.x + min(first_room.w - 1,2), first_room.y + min(first_room.h - 1,2)

    def place_player(self, player):
        player_x, player_y = self.player_position()
        self.board[player_x, player_y].occupant = player
