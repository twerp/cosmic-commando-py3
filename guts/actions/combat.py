'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.messages import message, infotip
import guts.grammar as grammar
from guts.game_data import game
from guts.utils import coinflip, random_pos, roll_dice, random_choice, eight_directions, directions, orientation
from guts.ai import Confusion
from guts.task_resolution import resolve_task
from guts.geometry import Line, distance, Point

def _damage(factor):
    return roll_dice(factor,7)

def _expend_ammo(action, agent):
    weapon = action.piece
    if weapon.flag('heats'):
        if weapon['heat'] < weapon['heat capacity']:
            weapon['heat'] += action['heat']
            if weapon['heat'] > weapon['heat capacity']:
                msg_text = "{0} {1} has overheated!".format(grammar.possessive(agent), weapon.name)
                message(msg_text, 'heat')
                if agent.is_player():
                    msg_text += " {0} won't be able to use it again until it cools down!".format(grammar.capitalise(agent.name))
                    infotip(msg_text, 'heat')
                    if action.requires_target:
                        action.requires_target = False
                        action['requires target'] = True
        else:
            infotip("{0} {1} has not cooled down enough yet!".format(grammar.possessive(agent), weapon.name), 'heat')
            return False
    return True

def closest_agent(x, y, max_range = None, include_player = True):
    current_distance = 1
    if max_range == None:
        max_range = max(game.board.width, game.board.height) 
    while current_distance <= max_range:
        agents = [tile.occupant for tile in game.board.ring(x, y, current_distance) \
                  if tile.visible and tile.occupant is not None and (include_player or not tile.occupant.is_player())]
        if agents:
            return random_choice(agents)
        current_distance += 1
    return None

def use_grenade(action, agent, target= None):
    weapon = action.piece
    if weapon['stack'] == 0:
        message("Your grenade box is empty!", weapon.color)
        return False
    if weapon['primed']:
        throw_grenade(action, agent, target)
        weapon['primed'] = False
        #weapon.name = weapon.name.replace('loaded', 'unloaded')
        action.requires_target = False
        weapon['stack'] -= 1
        weapon.color = weapon['unprimed color']
    else:
        if not 'unprimed color' in weapon:
            weapon['unprimed color'] = weapon.color
        weapon.color = weapon['primed color']
        action.requires_target = True
        weapon['primed'] = True
        weapon['primed timer'] = 0
        #weapon.name = weapon.name.replace('unloaded', 'loaded')
        message("{1} {2} {3} {0}.".format(weapon.name, agent.name, grammar.conjugate('prime', agent),
                                          grammar.possessive_pronoun(agent)), weapon.color)
    return True

def throw_grenade(action, agent, target):
    weapon = action.piece
    _expend_ammo(action, agent)
    hit = not Line(agent, target).is_blocked() or coinflip()
    x, y = target.x, target.y
    msg = ''
    if not hit:
        if agent.is_player():
            msg += "Your aim is a little off."
        deviation = random_choice(eight_directions)
        x += deviation[0]
        y += deviation[1]
    msg += ("{0} {1} {2}. It explodes, hurting everyone within blast radius ({3})!".format(
                agent.name, grammar.conjugate(action['verb'], agent),
                grammar.articled(weapon.name), action['radius']
                ))
    message(msg)
    tiles_in_blast = game.board.circle(x,y,action['radius'])
    for tile in tiles_in_blast:
        game.gfx(tile.x, tile.y, action['gfx color'])
        if tile.occupant is not None:
            damage = _attack(action, agent, tile.occupant)
            tile.occupant.take_damage(damage)

def mark_agent(action, agent, target):
    #every action automatically saves the target as action['last target'], which this will be used for
    target[action['flag']] = True
    target.color = action.piece.color 
    message(action['msg'].format(agent.name, target.name), action['msg color'])


def blow_up(action, agent, target):
    message("The {0} explodes, razing the ground!".format(action.piece.name), 'fiery')
    if target.occupant is not None:
        damage, advantages = _attack(action, agent, target.occupant)
        damage += advantages
        if damage > 0:
            target.occupant.take_consequences(damage, 'damage', 'permanent')
        elif damage < 0:
            agent.take_consequences((-1) * damage, 'damage', 'temporary')
            
        elif damage <= 0:
            message("{0} {3} {1} {2}{4}".format(agent.name, grammar.conjugate('miss', agent), target.occupant.name, 
                        'critically' if damage < 0 else '', '.' if damage == 0 else ', hurting yourself!' if agent.is_player() else ', hurting itself!'
                                                ))
        if damage < 0:
            agent.take_consequences((-1) * damage, 'damage', 'permanent')
    if target.feature is not None:
        message("The {0} destroys {1}!".format(action.piece.name, target.feature.name), 'fiery')
        target.feature = None
    target.terrain.name = 'blackpowder-blasted ground' 
    target.terrain.shape = 'star'
    target.terrain.color = 'grave grey'
    target.terrain.unset('blocks sight')
    target.terrain.unset('blocking')
    game.change_visibility_at(target.x, target.y) 
    return True

def deploy_feature(action, agent, target = None):
    """ TODO: This is a quite specific function, tailored for the projected shield. Generalize. 
    """
    if action.piece['deployed']:
        #TODO: breaks if board changes after deployment
        message("{0} {1}!".format(agent.name, action.piece.name.replace(' s', ' your s')), action.piece.color) #TODO: SUPER UGLY HACK FOR PROJECTED SHIELD
        x, y = action['feature']
        action['feature'] = game.board[x,y].feature
        game.board[x,y].feature = None
        action.piece['deployed'] = True
        if 'undeployed name' in action:
            action.piece.name = action['undeployed name']
        action.piece['deployed'] = False
        if action['feature'].flag('blocks sight'): 
            game.change_visibility_at(target.x, target.y) 
        action.requires_target = True    
        
    else:
        if target.feature is not None:
            message("{0} can't be deployed there because of {1}!".format(action['feature'].name, target.feature.name), 'warning')
            return False
        message("{0} {1} the {2}.".format(agent.name, grammar.conjugate('deploy', agent), action.piece.name), action.piece.color)
        target.feature = action['feature']
        action.piece['deployed'] = True
        action.requires_target = False
        action['feature'] = (target.x, target.y)
        if 'deployed name' in action:
            action['undeployed name'] = action.piece.name 
            action.piece.name = action['deployed name']
        if target.feature.flag('blocks sight'):
            game.change_visibility_at(target.x, target.y) 
    return True

def trait_transfer(action, agent):
    """ Damage transfer, actually."""
    successes, advantages = resolve_task(agent['attitude'],agent['skill'], agent['luck'], agent['confidence'])
    successes += 1
    advantages += 1
    if successes > 0 or advantages > 0:
        message(action['msg'], action['msg color'])
        if successes > 0:
            agent.take_consequences(successes, action['from'], 'permanent')
            agent.take_consequences(successes, action['to'], 'permanent')
        if advantages > 0:
            agent.take_consequences(advantages, action['side effect'], 'temporary')
    else:
        message("You've dropped your {0} before you could use it.".format(action.piece.name))
    return True

def chain_lightning(action, agent):
    if not _expend_ammo(action, agent):
        return False
    dmg_dice, current_range = action['damage'], action['range']
    x = agent.x
    y = agent.y
    while dmg_dice > 0:
        target = closest_agent(x, y, current_range, include_player = action['friendly fire'])
        if target is None:
            infotip('No enemy in range.', 'failure')
            break
        else:
            dmg = _damage(dmg_dice)
            message('Electricity arcs to {0}. Damage due to electrocution is {1}.'.format(target.name, dmg), 'electric')
            target.take_damage(dmg)
            x, y = target.x, target.y
            if 'gfx color' in action:
                game.gfx(x, y, action['gfx color'])
        dmg_dice -= 1
    return True

def gun_bump_into(action, agent, target):
    weapon = action.piece
    if weapon.flag('heats') and weapon['heat'] >= weapon['heat capacity']: 
        action['damage'] = action['melee damage']
        return melee(action, agent, target)
    else:
        action['damage'] = action['ranged damage']
        return weapon['ranged'].execute(agent, target)

def project_cone(action, agent, target = None):
    """ Projects a cone. """
    weapon = action.piece
    if not _expend_ammo(action, agent):
        return False
    damage = _damage(action['damage'])
    message("{0} {1} at {2}{3} with {4}!".format(
        agent.name, grammar.conjugate("shoot", agent), target.name,
        'rself' if target.is_player() and agent.is_player() else '', grammar.articled(weapon.name)))
    p = Line(agent, target).points[1]
    for tile in game.board.cone(p.x, p.y, p.x - agent.x, p.y - agent.y, action['range']):
        current_damage = damage / (distance(p, tile) * 2 + 1)
        game.gfx(tile.x,tile.y, weapon.color)
        if tile.occupant is not None:
                message("{0} {1} for {2} damage!".format(action['msg'], tile.occupant.name,
                                                         current_damage), weapon.color)
                tile.occupant.take_damage(current_damage)
    return True

def shoot(action, agent, target = None):
    weapon = action.piece
    if not _expend_ammo(action, agent):
        return False
    hit = random_pos(game.player['sight']) >= distance(agent, target)
    if hit:
        damage = _attack(action, agent, target)  
        message("{0} {1} at {2}{3} with {4} for {5} damage!".format(
                agent.name, grammar.conjugate("shoot", agent), target.name,
                'rself' if target.is_player() and agent.is_player() else '', grammar.articled(weapon.name), damage))
        target.take_damage(damage)
    else:
        message("{0} {1} {2}.".format(agent.name, grammar.conjugate("miss", agent), target.name))
    return True

def confusing_melee(action, agent, target):
    target_health = target['health']
    melee(action, agent, target)
    if target_health > target['health'] and not target['dead']:
        confusion_duration = (target_health - target['health']) / 4
        confusion_duration = confusion_duration if confusion_duration > 0 else 1 
        Confusion(target, confusion_duration)
        message('The eyes of the {0} look vacant, as he starts to stumble around! Confusion will last {1} turn{2}.'. \
                format(target.name, confusion_duration, 's' if confusion_duration > 1 else '')
                , 'confusion')    
    
def shoot_or_reload(action, agent, target = None):
    weapon = action.piece
    if weapon['loaded']:
        shoot(action, agent, target)
        weapon['loaded'] = False
        #weapon.name = weapon.name.replace('loaded', 'unloaded')
        action.requires_target = False
        #TODO: spend ammo
    else:
        action.requires_target = True
        weapon['loaded'] = True
        #weapon.name = weapon.name.replace('unloaded', 'loaded')
        message("{1} reload{2} {3} {0}.".format(weapon.name,
                                                    agent.name, grammar.conjugate("reload", agent), grammar.possessive_pronoun(agent)
                                                    ), weapon.color)
    return True

def _attack(action, agent, target):
    #TODO: add a system for the game
    """
    successes, advantages = resolve_task(agent['attitude'],agent['skill'], agent['luck'], -target['defense'])
    if successes > 0:
        if 'damage' in action:
            dmg_base = action['damage']
        else:
            dmg_base = 1 
        damage = successes * dmg_base
    elif successes < 0:
        damage = successes
        pass
    else:
        damage = 0
    """
    damage = 0
    if 'shield damage' in action and 'shields' in target:
        damage += min(_damage(action['shield damage']), target['shields'])
        if damage > 0:
            message('{0} {3} overloads {1}{2} shields!'.format(grammar.possessive(agent), 
                        target.name, 'r' if target.is_player() else "'s", action.piece.name), 'stunning blue') 
    damage += _damage(action['damage']) #TODO: replace with damage calculations
    if 'health damage' in action and (damage > target['shields'] if 'shields' in target else 0 + target['armor'] if 'armor' in target else 0):
        damage += _damage(action['health damage'])
        message('{0} {2} drains {1} blood!'.format(grammar.possessive(agent), 
                        grammar.possessive(target), action.piece.name), 'blood red')
    return damage


def melee(action, agent, target):
    weapon = action.piece
    hit = coinflip() or coinflip()
    if hit:
        damage = _attack(action, agent, target)  
        message("{0} {1} {2} with {3} for {4} damage!".format(
                agent.name, grammar.conjugate("hit", agent), target.name, grammar.articled(weapon.name), damage))
        target.take_damage(damage)
    else:
        message("{0} {1} {2}.".format(agent.name, grammar.conjugate("miss", agent), target.name))
    return True        