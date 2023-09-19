'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.game_pieces import Terrain, Feature, Item
from guts.game_agents import Agent, Player, item_action_types
from guts.actions import new_action
from .debug import debug
from .ai import *

piece_flags = ['blocking', 'blocks sight']
agent_flags = ['dead']
item_flags = []

def _add_flags(piece, flags, set_flags = []):
    """ Adding flags to a piece's trait dictionary.
        By default the flags are unset,
        but they can be added as set.
    """
    for flag in flags:
        if not flag in piece:
            piece[flag] = flag in set_flags

def _init_piece(piece, piece_type, name):
    if name is None:
        piece['name'] = piece_type
    else:
        piece['name'] = name
    _add_flags(piece, piece_flags)

def _add_necessary_agent_traits(piece):
    """ Add necessary traits and flags to agent's dictionary
        without cluttering their definitions.
    """
    _add_flags(piece, agent_flags)
    for trait in ['health', 'shields']:
        if trait in piece and not 'max ' + trait in piece:
            piece['max ' + trait] = piece[trait]
    piece['velocity'] = (0,0)

def new_player(name = "you"):
    player = Player(shape = 'player', color = 'player',
                    flags = ['blocking'],
                    traits = {'sight': 8, 'health' : 100, 'shields' : 100}
                    )
    _init_piece(player, 'player', name)
    _add_necessary_agent_traits(player)    
    player_items = ['lightning launcher', 'projected shield', 'power fist', 'psychodelic injector', 'Blaster Buzzard', 'sonic shotgun'] + ["frag grenade"] * 8
    for item_type in player_items:
        item = new_item(item_type)
        player.receive(item)
    for item in player.inventory:
        player.equip(item, silently = True)    
    return player

def new_agent(agent_type, name = None):
    shape, color, flags, traits, equipment = agent_types.get((agent_type),
                        ('default', 'default', ['blocking'],
                         {'health': 100}, [])    
                        ) 
    if shape == 'default':
        debug.log("requested undefined agent type: " + str(agent_type))
    agent = Agent(shape = shape, color = color, flags = flags, traits = traits)
    _init_piece(agent, agent_type, name)
    _add_necessary_agent_traits(agent)
    for item_type in equipment:
        item = new_item(item_type)
        agent.receive(item)
        agent.equip(item)
    return agent

agent_types = {'Raven recruit': ('Raven soldier', 'Raven Rank 1', ['blocking'], {'health' : 50, 'shields': 25, 'ai': StandardSoldier()},
                                 ['riving rifle']),
               'Raven officer': ('Raven soldier', 'Raven Rank 2', ['blocking'], {'health' : 50, 'shields': 60, 'ai': StandardSoldier()},
                                 ['ravenous rapier', 'Rift Raven']),
               'Raven general': ('Raven soldier', 'Raven Rank 3', ['blocking'], {'health' : 50, 'shields': 60, 'ai': StandardSoldier()},
                                 ['ravenous rapier', 'Rift Raven']),
               'Raven security guard':  ('Raven soldier', 'Raven Rank 2', ['blocking'], {'health' : 50, 'shields': 50, 'ai': StandardSoldier()},
                                 ['stun gun']),
               'Raven scientist':  ('Raven soldier', 'white', ['blocking'], {'health' : 50, 'shields': 15, 'ai': StandardSoldier()},
                                 ['needler']),
               'Raven repairman': ('Raven soldier', 'omnitool', ['blocking'], {'health' : 50, 'shields': 15, 'ai': RelentlessMelee()},
                                 ['power tool']),
               'Raven spaceship pilot': ('Raven soldier', 'Raven Rank 3', ['blocking'], {'health' : 50, 'shields': 50, 'ai': StandardSoldier()},
                                 ['Rift Raven', 'butt of his gun']),
               'cybork' : ('cybork', 'metallic green', ['blocking'], {'health' : 100, 'armor':5, 'ai': RelentlessMelee()},
                                 ['power fist']),
               'Corvid-class Mech': ('mech', 'steel', ['blocking'], {'health' : 100, 'armor': 5, 'shields': 100, 'ai': StandardSoldier()},
                                     ['smart rocket', 'mechaclaw']),
               'Lady Raven' : ('Raven soldier', 'maroon', ['blocking'], {'health' : 50, 'armor': 2, 'shields': 60, 'ai': SelfDefense()},
                                    ['ravenous rapier']),
               'Space Pirate Captain Bluesteel' : ('Pirate', 'steel blue', ['blocking'], {'health' : 100, 'armor': 2, 'shields': 100,
                                                'speed': 3, 'looking for': 'Blue Crow', 'trajectory index': 0, 'ai': NavigateAsteroids()}, [])
              }

def _add_necessary_item_traits(piece):
    """ Add necessary traits and flags to agent's dictionary
        without cluttering their definitions.
    """
    _add_flags(piece, agent_flags)
    if piece.flag('stacks') and not 'stack' in piece:
        piece['stack'] = 1
    if piece.flag('heats') and not 'heat' in piece:
        piece['heat'] = 0
        piece['heat capacity'] = 10

def new_item(item_type, name = None):
    """ Item factory.
    """
    shape, color, flags, traits = item_types.get(item_type,
                ('default', 'default', [], {}))
                #new_action('feedback', {'feedback msg': 'This doesn\'t do anything.'}
    if shape == 'default':
        debug.log("requested undefined item type: " + str(item_type))
    item = Item(shape = shape, color = color, flags = flags, traits = traits)
    _init_piece(item, item_type, name)
    _add_necessary_item_traits(item)
    for action_type in item_action_types:
        if action_type in item:
            action_key, action_data = traits[action_type]
            item[action_type] = new_action(action_key, action_data)
            item[action_type].piece = item
            if 'feature' in item[action_type]:
                item[action_type]['feature'] = new_feature(item[action_type]['feature'])
    item['type'] = item_type
    return item
    
item_types = {'medkit' : ('medical', 'health', ['stacks'], 
                          {'consumable': ('replenish', {'trait': 'health', 'amount' : 50})}),
              "frag grenade" : ('grenade', 'military', ['stacks', 'smart aim'], 
                           {'primed': False, 'primed color': 'ui text', 'consumable': ('use grenade', {'damage': 7, 'radius': 1, 'verb':'throw', 'gfx color': 'fiery'})}),
              "EMP grenade" : ('grenade', 'shields', ['stacks', 'smart aim'], 
                           {'primed': False, 'primed color': 'stunning blue',
                            'consumable': ('use grenade', {'damage': 0, 'shield damage': 20, 'radius': 2, 'verb':'throw', 'gfx color': 'stunning blue'})}),
              'smart rocket' : ('grenade', 'military', ['smart aim', 'heats'], 
                           {'ranged': ('throw grenade', {'damage': 2, 'heat': 6, 'radius': 1, 'verb':'fire', 'gfx color': 'fiery'})}),
              
              'stimpack' : ('medical', 'health', ['stacks'], 
                            {'consumable': ('replenish', {'trait': 'health', 'amount' : 50})}),#TODO: do something else
              'projected shield' : ('shield', 'omnitool', ['close range'], {'deployed': False, 'deployable' : ('deploy feature', {'feature':'projected shield', 'deployed name': 'stop projecting shield'})} ),
              #ranged weapons
              'riving rifle' : ('ranged weapon', 'metallic', ['heats'], 
                               {'melee' : ('melee', {'damage' : 1}),
                                'ranged' : ('shoot', {'damage' : 2, 'heat': 3})}), 
              'sonic shotgun' : ('ranged weapon', 'ultrasound', ['heats', 'smart aim'], 
                               {'melee' : ('gunmelee', {'melee damage' : 3, 'ranged damage' : 6, 'range' : 3, 'msg': 'Sonic wave hits', 'heat': 6}),
                                'ranged' : ('scattershoot', {'damage' : 6, 'range': 3, 'msg': 'Sonic wave hits','heat': 6})}),
              'needler' : ('ranged weapon', 'white', [],
                            {'melee' : ('shoot', {'damage' : 1}), #TODO: shoot and inject confusion
                             'ranged' : ('shoot', {'damage' : 1})}),
              'stun gun'  : ('ranged weapon', 'white', ['heats'],
                            {'melee' : ('melee', {'heat': 0, 'damage' : 2, 'shield damage': 2}), 
                             'ranged' : ('shoot', {'heat': 3, 'damage' : 2, 'shield damage': 2})}),
              'Blaster Buzzard' : ('ranged weapon', 'metallic', ['heats'], { 'ranged': ('shoot', {'damage' : 4, 'heat': 4})}),
              'Rift Raven' : ('ranged weapon', 'metallic', ['heats'], { 'ranged': ('shoot', {'damage' : 3, 'heat' : 4})}),
              
              'lightning launcher' : ('ranged weapon', 'electric', ['heats'],
                                    {#'melee': ('melee', {'damage' : 2}),
                                     #'ranged': ('mark agent', {}),
                                     'activated': ('chain lightning', {'damage' : 3, 'range': 5, 'heat': 5, 'friendly fire': True, 'gfx color': 'electric'})}),
              'debug launcher' : ('ranged weapon', 'electric', ['heats'],
                                    {#'melee': ('melee', {'damage' : 2}),
                                     #'ranged': ('mark agent', {}),
                                     'activated': ('chain lightning', {'damage' : 100, 'range': 20, 'heat': 1, 'friendly fire': False})}),
              
              #melee weapons
              'ravenous rapier': ('melee weapon', 'blood red', [], 
                            {'melee': ('melee', {'damage' : 3, 'health damage': 3})}), 
              'gauntlet' : ('melee weapon', 'metallic', [], {'melee': ('melee', {'damage' : 2})}), 
              'butt of his gun' : ('melee weapon', 'metallic', [], {'melee': ('melee', {'damage' : 1})}),
              'mechaclaw' : ('melee weapon', 'metallic', [], {'melee': ('melee', {'damage' : 4})}),
              'power fist': ('melee weapon', 'stunning blue', [], 
                            {'melee': ('melee', {'damage' : 3, 'shield damage': 3})}),
              'power tool': ('melee weapon', 'stunning blue', [], 
                            {'melee': ('melee', {'damage' : 2, 'shield damage': 2})}),
              'psychodelic injector': ('melee weapon', 'metallic', [], {'melee': ('confusing melee', {'damage' : 2})}), #confuses on health hit
              'submission net': ('melee weapon', 'submission', [], {'melee': ('mark agent', 
                                {'msg': "{0} entangle and incapacitate {1} in the submission net." , 'msg color' : 'submission', 'flag':'incapacitated'} )})
             }

def new_feature(feature_type, name = None):
    shape, color, flags, interaction = feature_types.get(feature_type,
                        ('default', 'default', [],
                          new_action('feedback', {'msg': 'Default action.'})))
    if shape == 'default':
        debug.log("requested undefined feature type: " + str(feature_type))
    feature = Feature(shape = shape, color = color, flags = flags, interaction = new_action(interaction[0], interaction[1]))
    _init_piece(feature, feature_type, name)
    return feature

feature_types = {'closed door' : ('closed door', 'metallic gray', ['closed', 'blocking', 'blocks sight'], ('door', {'open shape':'open door'})),
                 'lab workstation' : ('terminal', 'white', ['blocking'], \
                                     ('mission', {'msg' : ('You sabotage lab equipment.','gold'), \
                                                  'done msg': ('You have already sabotaged this workstation.', 'gray'), \
                                                  'done color': 'gray',
                                                  'objective': 'lab sabotage'})),
                 'data console' : ('terminal', 'grave grey', ['blocking'], \
                                     ('mission', {'msg' : ('You download secret Raven files from this console.','gold'), \
                                                  'done msg': ('You have already downloaded data from this console.', 'gray'), \
                                                  'done color': 'gray',
                                                  'objective': 'find data'})),
                 'spaceship cockpit w/iff' : ('terminal', 'steel blue', ['blocking'], \
                                     ('mission', {'msg' : ("You rip a Raven IFF from the pilot's dashboard. This one is functional and we'll do nicely.",'gold'), \
                                                  'done msg': ('You have already ravaged this starship cockpit. The damaged machinery sparkles.', 'omnitool'), \
                                                  'done color': 'omnitool',
                                                  'objective': 'iff'})),
                 'spaceship cockpit' : ('terminal', 'steel blue', ['blocking'], \
                                     ('flavor', {'msg' : ("You rip a Raven IFF from the pilot's dashboard, damaging it in the process. You must find a different one.",'omnitool'), \
                                                  'touched msg': ('You have already ravaged this starship cockpit. The damaged machinery sparkles.', 'omnitool'), \
                                                  'touched color': 'omnitool',
                                                  })),
                 'spaceship hull' : ('wall', 'steel', ['blocking', 'blocks sight'], ('feedback', {'msg': ('The hull of a spaceship.', 'steel')})),
                 'repair cart' : ('rubble', 'omnitool', ['blocking'], ('feedback', {'msg': ('A cart full of tools needed by the repairmen.', 'omnitool')})),
                 'projected shield' : ('shield', 'omnitool', ['blocking'], ('feedback', {'msg': ('This transparent projected shield protects you from enemy fire without reducing visibility. ' \
                                                     'It will automatically fold if you move away from it, but you can maneuver around it.','omnitool')})),
                 'asteroid': ('wall', 'dark wooden', ['blocking', 'blocks sight'], ('feedback', {'msg': ("A rock, floating in the void.", 'dark wooden')})),
                 'Blue Crow': ('terminal', 'steel blue', ['blocking', 'npc only'], 
                            ('mission', {'msg' : ('Space Pirate Captain Bluesteel gets away in the Blue Crow!','steel blue'), 'objective': 'pirate getaway'}))
                }

def new_terrain(terrain_type, name = None):
    shape, color, flags = terrain_types.get(terrain_type, ('default', 'default', []))
    if shape == 'default':
        debug.log("requested undefined terrain type: " + str(terrain_type))
    terrain = Terrain(shape, color, flags)
    _init_piece(terrain, terrain_type, name)
    return terrain

terrain_types = {'wall' : ('wall', 'metallic gray', ['blocking', 'blocks sight']),
                 'floor' : ('floor', 'metallic gray', []),
                 'lab floor' : ('floor', 'white', []),
                 'blood-spattered floor' : ('floor', 'blood red', []), 
                 'slime-covered floor' : ('floor', 'metallic green', []),
                 'lab wall' : ('wall', 'white', ['blocking', 'blocks sight']),
                 'way off the spaceport': ('floor', 'omnitool', ['blocking']),
                 'spacestrip': ('floor', 'steel', []),
                 'void': ('nothing', 'black', ['zero g']),
                 'starry void': ('starry', 'white', ['zero g']),
                 'holowall' : ('wall', 'omnitool', [])
                }



    
