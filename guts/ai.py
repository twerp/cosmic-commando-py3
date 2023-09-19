'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.game_data import game
from guts.utils import *
from guts.messages import message
from guts.geometry import Line, distance, Point

class AI(object):
    """ Don't put any variables in the AI, because agents often share AI objects.
        Besides, pieces such as agents are perfectly good dictionaries and they never
        exchange AIs.  
    """
    
    def act(self, agent):
        """ A virtual method, so to speak."""
        raise Exception("Unimplemented AI method : " + self.__class__.__name__)

    def go_for_melee(self, agent, target):
        if distance(agent, target) > 1:
            self.move_towards(agent, target)
        else:
            agent.melee(target)

    def go_for_ranged(self, agent, target):
        """ The agent tries to position itself to get a clean shot
            at the target or fires or 
            tries to move away from the target if unable to shoot.
        """
        line = Line(agent, target)
        found_a_line_of_fire = False 

        if (agent['ranged item'].flag('smart aim') or not line.is_blocked()) and not (agent['ranged item'].flag('heats') and agent['ranged item']['heat'] >= agent['ranged item']['heat capacity']):
            found_a_line_of_fire = True
            agent.shoot(target)
        else:
            for dx,dy,_ in sorted(self.available_moves(agent, target), key = lambda direction: direction[2], reverse = True):
                if not Line(Point(agent.x + dx, agent.y + dy), target).is_blocked():
                    agent.move_to(agent.x + dx, agent.y + dy)
                    found_a_line_of_fire = True
                    break
        if not found_a_line_of_fire:
            self.move_away(agent, target)
            
    def available_moves(self, agent, target = None):
        acceptable_directions = []
        for dpos in eight_directions:
            dx, dy = dpos
            p = Point(agent.x + dx, agent.y + dy)
            if not game.board[p.x,p.y].is_blocked():
                acceptable_directions.append((dx, dy, distance(p, target) if target is not None else None))
        return acceptable_directions
    
    def move_away(self, agent, target):
        acceptable_directions = self.available_moves(agent, target)
        if len(acceptable_directions) == 0:
            agent.wait()
        else:
            dx, dy, _ = sorted(acceptable_directions,key=lambda direction: direction[2], reverse = True)[0]
            x, y = agent.x + dx, agent.y + dy
            agent.move_to(x,y)
        
    def move_towards(self, agent, target):
        acceptable_directions = self.available_moves(agent, target)
        if len(acceptable_directions) == 0:
            agent.wait()
        else:
            dx, dy, _ = sorted(acceptable_directions,key=lambda direction: direction[2])[0]
            x, y = agent.x + dx, agent.y + dy
            agent.move_to(x,y)

    def store_previous(self, agent):
        if 'previous ai' not in agent:
            agent['previous ai'] = []
        agent['previous ai'].append(agent['ai'])

    def restore_previous(self, agent):
        agent['ai'] = agent['previous ai'].pop()
    
    def random_step(self, agent):
        x = agent.x + random_int(-1, 1)
        y = agent.y + random_int(-1, 1)
        if game.board[x,y].is_blocked():
            if not game.board[x,y].occupant == agent:
                message("{0} bumps into {1}.".format(agent.name, game.board[x,y].blocking_piece))
            else:
                message("{0} spins around in confusion.".format(agent.name))
        else:
            agent.move_to(x,y)

class RelentlessMelee(AI):
    
    def act(self, agent):
        if game.is_visible(agent):
            self.go_for_melee(agent, game.player)
        else:
            agent.wait()

class StandardSoldier(AI):
    
    def act(self, agent):
        if game.is_visible(agent):
            if distance(agent, game.player) == 1:
                self.go_for_melee(agent, game.player)
            else:
                self.go_for_ranged(agent, game.player)
        else:
            agent.wait()

class SelfDefense(AI):
    
    def act(self, agent):
        if game.is_visible(agent):
            if distance(agent, game.player) == 1:
                self.go_for_melee(agent, game.player)
            else:
                self.move_away(agent, game.player)
        else:
            agent.wait()

class Confusion(AI):
    
    def __init__(self, target, duration):
        AI.__init__(self)
        self.store_previous(target)
        target['confusion duration'] = duration
        target['ai'] = self
    
    def act(self, agent):
        if agent['confusion duration'] == 0:
            self.restore_previous(agent)
            if not isinstance(agent['ai'], Confusion):
                message('The ' + agent.name + ' is no longer confused!', 'clarity')
                del agent['confusion duration']
                del agent['previous ai']
        else:
            agent['confusion duration'] -= 1
            self.random_step(agent) 

class NavigateAsteroids(AI):
    
    #TODO: move trajectory computation here
    
    def act(self, agent):
        if not agent.flag('incapacitated'):
            if agent['trajectory index'] == len(agent['trajectory']):
                for dx,dy in eight_directions:
                    x,y = agent.x + dx, agent.y + dy
                    if game.board[x,y].feature is not None and game.board[x,y].feature.name == agent['looking for']:
                        game.board[x,y].feature.interact(agent)
                        agent.leave()
                        break
            else:
                fx, fy = None, None
                for _ in range(agent['speed']):
                    x,y = agent['trajectory'][agent['trajectory index']]
                    if game.board[x,y].occupant is not None:
                        game.board[x,y].occupant.melee(agent)
                        break
                    else:
                        fx, fy = x,y
                    agent['trajectory index'] += 1
                if fx is not None:
                    agent.move_to(fx,fy) 
        
#__all__ = ['RelentlessMelee', 'StandardSoldier', 'Confusion']    