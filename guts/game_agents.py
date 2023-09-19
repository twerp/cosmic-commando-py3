'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.debug import debug
from guts.game_data import game
from guts.messages import message, infotip
from guts.game_piece import Piece
from guts.game_description import trait_level_description, describe_item
from guts.geometry import distance, Point
from guts import grammar

item_action_types = ['melee', 'ranged', 'activated', 'consumable', 'deployable']

class Agent(Piece):
    
    def __init__(self, *args, **kwargs):
        Piece.__init__(self, *args, **kwargs)
        self['role'] = 'unknown'
        self.inventory = []
        for flag in item_action_types:
            self[flag + ' item'] = None

    def leave(self):
        game.board[self.x, self.y].occupant = None
        
    def _arrive_on(self, tile):
        tile.occupant = self
    
    def change_role(self, role):
        self['role'] = role

    def is_player(self):
        return self['role'] == 'player'


    
    """
    def take_consequences(self, amount, consequence, duration):
        if self.flag('dead'):
            return None
        assert(amount >= 0)
        trait_affected = consequence if consequence in traits else trait_losses[consequence]
        max_trait = self['max ' + trait_affected] if trait_affected in ['health', 'stamina'] else 3
        min_trait = 0 if trait_affected in ['health', 'stamina'] else -3
        
        original_trait_value = self[trait_affected]
        if consequence in trait_losses:
            self[trait_affected] = max(min_trait, original_trait_value - amount)
        else:
            self[trait_affected] = min(max_trait, original_trait_value + amount)
        amount = (original_trait_value - self[trait_affected]) * (1 if consequence in trait_losses else -1)
        #TODO: spillover -> stamina -> health
        
        if duration != 'permanent':
            assert duration in ['temporary', 'tactical']
            self[duration + ' ' + trait_affected] += amount
        if trait_affected is not None:
            message("{0}{1} {2} {5}{6}{3}s by {4}.".format(self.name, 'r' if self.is_player() else "'s",
                                                     trait_affected, "decrease" if consequence in trait_losses else "increase",
                                                     amount if amount >= 0 else -amount, duration_description(duration),
                                                     ' ' if len(duration_description(duration)) > 0 else ''), consequence)
        if self['health'] == 0:
            self.death()

    def _refresh(self, duration):
        refreshed = False
        for trait in traits:
            if self[duration + ' ' + trait] != 0:
                self.take_consequences(self[duration + ' ' + trait],
                                       trait if self[duration + ' ' + trait] >0 else trait_gains[trait], 'permanent')
                self[duration + ' ' + trait] = 0
                refreshed = True
        if self['ranged item'] is not None:
            if not self['ranged item']['loaded']:
                self['ranged item'].use(self, 'ranged')
                refreshed = True
        return refreshed
        
    def refresh(self, full = False):
        #tactical refresh
        refreshed = self._refresh('tactical')
        if full:
            refreshed = refreshed or self._refresh('temporary')
        return refreshed
    """

    def recharge(self):
        if 'shields' in self and self['shields'] < self['max shields']:
            self['shields'] = min(self['max shields'], self['shields'] + self['shield recharge'])
            self['shield recharge'] += 1
            if self['shields'] == self['max shields'] and game.is_visible(self): 
                message('{0}{1} shields are fully restored!'.format(self.name, 'r' if self.is_player() else "'s"), 'full shields')
        if self['deployable item'] is not None and self['deployable item']['deployed']:
            #TODO: this is temporary, projected shields should have an effect attached that will fold them
            #though, perhaps, this is were attached effect will fire off
            if distance(self, Point(*self['deployable item']['deployable']['feature'])) > 1:
                self['deployable item'].use(self, 'deployable')
        for item in [item for item in self.inventory if 'primed' in item]:
            #TODO: effects needed stat!
            if item['primed']:
                primer_max_time = 3 
                if item['primed timer'] >= primer_max_time:
                    item['primed'] = False
                    for action_type in item_action_types: #TODO: dangerous hack. Needs to merge with use_grenade in guts.actions.combat!
                        if action_type in item:
                            item[action_type].requires_target = False
                    item.color = item['unprimed color']
                    message("{0} reengages safety mechanisms.{1}".format(item.name, ' Prime it again before using.' if self.is_player() else ''), item.color)
                else:
                    message("{0} priming countdown: {1}...".format(item.name, primer_max_time - item['primed timer']), item.color)
                    item['primed timer'] += 1
        for item in [item for item in self.inventory if item.flag('heats')]:
            if item['heat'] > 0:
                item['heat'] -= 1
                if item['heat'] < item['heat capacity']:
                    for action_type in item_action_types:
                        if action_type in item:
                            if 'requires target' in item[action_type] and item[action_type]['requires target']:
                                item[action_type].requires_target = True
                                #TODO: another ugly hack that requires an effect framework
        
                
    def take_damage(self, damage):
        damaged_trait = None
        if damage > 0:
            if 'shields' in self:
                self['shield recharge'] = 0
                if damage > self['shields']:
                    damage -= self['shields']
                    self['shields'] = 0
                else:
                    self['shields'] -= damage
                    damage = 0
                    damaged_trait = 'shields'
            if 'armor' in self:
                damage = 0 if self['armor'] >= damage else damage - self['armor']
            if damage > 0:
                self['health'] -= damage
                if self['health'] <= 0:
                    self.death()
                    damaged_trait = None
                else:
                    damaged_trait = 'health'
        if damaged_trait is not None and not self.is_player():
            trd = trait_level_description(damaged_trait, self)
            message("{0} has {1}.".format(self.name, trd), trd)
        else:
            if not self['dead'] and damaged_trait is None:
                message("{0} {1} too thick an armor to be hurt.".format(self.name, 'have' if self.is_player() else 'has'), 'metallic gray')

    def death(self):
        message(self.name + " dies!", 'frag')
        if not self.is_player():
            game.note_death(self)
        #for item in [item for item in self.inventory]:
        #item.drop(self)
        self.become_corpse()
        self['dead'] = True
        self.ai = None
        self.leave()
    
    def become_corpse(self):
        #TODO: corpses! 
        '''monster.char = 'corpse'
        monster.color = 'dark_red'
        monster.name = 'remains of ' + monster.name
        '''
        pass

    def act(self):
        self['ai'].act(self)

    def wait(self):
        pass

    def drop(self, item):
        # remove from agent's inventory and put it on the tile the agent is standing on.
        self.inventory.remove(self)
        game.board[self.x, self.y].put(self)
        if self.is_player():
            message('You dropped a ' + self.name + '.')

    def pick_up(self, item):
        """ TODO: inventory limits or carrying capacity or both
        if 'carrying capacity' in agent: 
        if len(Game().inventory) >= 26:
            infotip('Your inventory is full, cannot pick up ' + self.owner.name + '.', 'warning')
        else:
        """
        game.board[item.x, item.y].remove(item)
        self.receive(item)
        if self.is_player:
            message('You picked up {0}!'.format(describe_item(item), 'positive'))

    def receive(self, item):
        if item.flag('stacks') and item['type'] in [inv_item['type'] for inv_item in self.inventory]:
            item_stack = filter(lambda f_item : f_item['type'] == item['type'], self.inventory)[0]
            item_stack['stack'] += item['stack']
        else:
            self.inventory.append(item)

    def equip(self, item, silently = False):
        message_fired = silently
        items_to_remove = []
        items_to_equip = {}
        for action_type in item_action_types:
            if action_type in item:
                if self[action_type + ' item'] != item:
                    items_to_remove.append(self[action_type + ' item']) #don't unequip items. only switching allowed.
                    self[action_type + ' item'] = item
                    if not message_fired and self.is_player() or game.is_visible(self):
                        message("{0} equip{1} {2}.".format(self.name, '' if self.is_player() else 's', describe_item(item)), 'positive')
                        message_fired = True
        for action_type in item_action_types:
            items_to_equip = []
            for inv_item in self.inventory:
                if action_type in inv_item and inv_item not in items_to_remove:
                    items_to_equip.append(inv_item)
            if self[action_type + ' item'] in filter(None, items_to_remove):
                #TODO: this code only works for Blaster Buzzard specifically, otherwise it can break item slottage
                if len(items_to_equip)!=1:
                    self[action_type + ' item'] = None 
                else:
                    self[action_type + ' item'] = items_to_equip[0]
                    message("{0} equip{1} {2}.".format(self.name, '' if self.is_player() else 's', describe_item(items_to_equip[0])), 'positive')
        if not silently:
            for equipped_item in filter(None, items_to_remove):
                message("{0} unequip{1} {2}.".format(self.name, '' if self.is_player() else 's', describe_item(equipped_item)), 'negative')
        #TODO: apply passive effects

    def melee(self, target = None):
        if self['melee item'] is None:
            if self.is_player():
                infotip("Funny - you never learned how to fight bare-handed. Better try another approach if you want to harm {0}.".format(target.name), 'warning')
                return False
            else:
                debug.log(self.name + " has no melee item, but tries to melee something.")
        else:
            self['melee item'].use(self, 'melee', target)
            return True

    def shoot(self, target = None):
        self['ranged item'].use(self, 'ranged', target)
        
    def apply_velocity(self):
        #TODO: rethink the approach - shouldn't this be generalised as an attached effect of velocity movement?
        def velocity_vector(x, y, dx, dy, board):
            if dx == dy == 0:
                return []
            #TODO: this probably could be written in one lambda function
            mod_x, mod_y = 0,0
            if abs(dx) == abs(dy):
                mod_x = dx/abs(dx)
                mod_y = dy/abs(dy)
            elif abs(dx) > abs(dy):
                mod_x = dx/abs(dx)
            else:
                mod_y = dy/abs(dy)
            final_x, final_y = board.adjust_to_bounds(x + mod_x, y + mod_y)
            return [(final_x, final_y)] + velocity_vector(final_x, final_y, dx - mod_x, dy - mod_y, board)
        vx, vy = self['velocity']
        last_x, last_y = self.x, self.y
        for x,y in velocity_vector(self.x, self.y, vx, vy, game.board):
            tile = game.board[x,y] 
            if tile.is_blocked():
                if tile.occupant is not None and tile.occupant != self:
                    self.melee(tile.occupant) #fly by attack!
                elif tile.occupant is not None and tile.occupant == self:
                    #TODO: edge case: adjustment to stay in board doesn't let the agent move
                    message("{0} {1} too far away, out of scope of this mission!".format(self, grammar.conjugate("drift", self)), 'failure')
                    self['drifted off'] = True
                    self.leave()
                    return
                else:
                    speed = max(abs(vx), abs(vy))
                    damage = 10 * speed ** 2
                    message("{0} {1} into {2}, taking {3} damage!".format(self.name, grammar.conjugate("crash", self), grammar.articled(tile.blocking_piece.name), damage), 'warning')
                    self.take_damage(damage)
                    self['velocity'] = (0,0)
                    break
            else:
                last_x, last_y = x,y
                game.fov_recompute = True
        self.move_to(last_x, last_y)
        if self.color in game.overlays:
            for coords in game.overlays[self.color]:
                del game.overlays[coords]
            del game.overlays[self.color]
        for coords in velocity_vector(self.x, self.y, self['velocity'][0], self['velocity'][1], game.board):
            game.overlays[coords] = self.color
            if self.color not in game.overlays:
                game.overlays[self.color] = []
            game.overlays[self.color].append(coords)
        
class Player(Agent):

    def __init__(self, *args, **kwargs):
        Agent.__init__(self, *args, **kwargs)
        self['role'] = 'player'
        
    def _arrive_on(self, tile):
        Agent._arrive_on(self, tile)
        
    def death(self):
        message('You died!','blood red')
        game.state = 'dead'
        self['dead'] = True
        #for added effect, transform into a corpse!
        #TODO: actual dropping of a corpse in case of teamplay - probably just needs a switch in agent death()
        self.shape = 'corpse'
        self.color = 'blood red'
        infotip('Press <SPACE> or <ESC> to go back to main menu', 'important')

    def shoot(self, target):
        self['ranged item'].use(self, target)
        
