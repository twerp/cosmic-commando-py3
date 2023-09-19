'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from . import libtcodpy as libtcod
from .debug import debug

default_color = libtcod.Color(0xff, 0x69, 0xb4) # hot pink ;)
default_shape = libtcod.CHAR_BLOCK3

shapes = {'space' : ' ', 'floor' : '.', 'water' : '~', 'wall' : '#', 'overgrown floor': ';',
          'starry': '`', 'double starry': ':', 'single starry': '.',
          'window' : '-',
          'nothing' : ' ',
          'terminal' : '&', 'rubble' : '%', 
          'closed door':'|', 'open door':':', 
          'stairs down' : '>', 'stairs up' : '<', 'stairs next' : '>', 'stairs prev' : '<',
          'shield' : ']',
          'corpse' : '%',
          'player' : '@',
          #'human' : '@', 'person' : '@',
          'Raven soldier' : 'R', 'cybork' : 'O', 'mech' : 'M', 'drone': 'D', 'Pirate': 'P',
          'medical' : '+', 'ranged weapon' : '{', 'melee weapon' : '/', 'grenade' : '?',
          'n/a' : default_shape
          }
   
def _c(r,g,b):
    """ Shortening the notation. """
    return libtcod.Color(r,g,b) 
    
colors = {'n/a': default_color,
          'black': libtcod.black, 'white': libtcod.white, 'joke': default_color,
          'gold':  _c(255, 0xD7, 0), 'gray': _c(128,128,128),
          'player': _c(250, 59, 26),
          'ui' : _c(250, 59, 26), 'ui text' : _c(60, 248, 0),
          'completed quest': libtcod.lightest_amber, 'tracked quest': libtcod.light_amber, 'optional quest': libtcod.lighter_amber,
          #fallout rl colours
          'normal_text': _c(60, 248, 0), 'warning_text': _c(155, 41, 37), 'highlighted_text': _c(245, 243, 168), 'faded_text': _c(29, 46, 27),
          'target clear': _c(50, 205, 50), 'target blocked': _c(178,34,34),

          #TODO: name colors:
          'frag' : libtcod.light_orange, 'failure': libtcod.magenta, 'confusion': libtcod.light_green, 'clarity' : libtcod.light_cyan,

          'ion' : _c(157,197,207),
          'heat': _c(255,69,18), 'heat capacity': _c(63, 17, 5),
          'ultrasound' : _c(99, 79, 148), 'ultraviolet': _c(99, 79, 148),
          'lead pellets': _c(188, 178, 168),
          'stunning blue': _c(97,125,255),
          'fire brick': _c(178, 34, 34),
          'lime green': _c(50, 205, 50),
          'unique' : libtcod.gold,
          'military': _c(70,96,49), 
          'electric': libtcod.light_cyan,
          'dirty brown' : libtcod.sepia,
          'inky black': libtcod.darkest_blue,
          'dusty gray': libtcod.gray,
          'grave grey': libtcod.dark_grey,
          'bone white': libtcod.lightest_gray,
          'deathly white' : libtcod.white,
          'cursed yellow': libtcod.dark_yellow,
          'dark wooden' : libtcod.dark_sepia,
          'wooden' : libtcod.sepia,
          'copper' : _c(193, 114, 73),
          'light watery' : _c(172, 220, 218),  
          'sandy': _c(223, 203, 141),
          'fashionable' : libtcod.light_purple,
          'mellow' : _c(172, 216, 180),
          'angry': _c(255, 0, 0),
          'fiery': _c(255, 127, 0),
          'maroon': _c(176, 48, 96),          
          'steel' : _c(176,196,222), #light steel blue
          'submission': _c(245, 225, 225),
          'Huginn': libtcod.white, 
          'Muninn': libtcod.white,
          'A Murder of Crows': libtcod.white, 
          "Raven's Nest": libtcod.gray,
          'Asteroid Belt Chase':libtcod.lighter_sepia,
          
          'omnitool': _c(255,168,0),
          'metallic green' : _c(161,203,121), 'metallic gray' : _c(162,162,162), 'metallic' : _c(162,162,162),
          'shields': libtcod.blue,'full shields' : _c(155,195,255), 'nearly full shields' : _c(115,155,225), 'still strong shields'  : _c(75,115,195), 'weakened shields' : _c(35,75,165), 'waning shields' : libtcod.darker_blue,
          'health': libtcod.red,'full health' : _c(255,225,225), 'nearly full health' : _c(255,180,180), 'still strong health'  : _c(255,120,120), 'weakened health' : _c(255,60,60), 'waning health' : _c(255,0,0),

          'positive': libtcod.light_green, 'warning': libtcod.orange, 'negative': libtcod.red,
          'out of sight' : libtcod.darker_gray,
          'important' : libtcod.light_yellow,
          
          'objective fulfilled': libtcod.gold, 'objective available': libtcod.white, 'objective unavailable': libtcod.gray, 
          'quest ': libtcod.pink,
          
          'star class O': _c(167,132,255), 'star class B': _c(181,159,255), 'star class A': _c(208,197,255),
          'star class F': _c(248,243,255), 'star class G': _c(248,242,229), 'star class K': _c(241,214,146),'star class M': _c(241,217,85),
          
          'Test 1': libtcod.light_pink, 'Test 2': libtcod.light_pink, 'Test Zero G': libtcod.light_pink, 'Test Final': libtcod.light_pink,
          'hot pink' :  libtcod.Color(0xff, 0x69, 0xb4),
          'blood red': libtcod.darker_red,
		  'steel blue': _c(70, 130, 180),
          'Raven Rank 1' : _c(105,105,105), 'Raven Rank 2' : _c(155,155,155), 'Raven Rank 3' : _c(205,205,205), 'Raven Rank 4' : _c(255,255,255),
          'metallic green' : _c(161,203,121), 'metallic gray' : _c(162,162,162), 'metallic' : _c(162,162,162),
          'shields': libtcod.blue,'full shields' : _c(155,195,255), 'nearly full shields' : _c(115,155,225), 'still strong shields'  : _c(75,115,195),
          'weakened shields' : _c(35,75,165), 'waning shields' : libtcod.darker_blue, 'no shields': libtcod.darkest_blue,
          'health': libtcod.red,
          'full health' : _c(255,225,225),
          'no injuries' : _c(255,225,225), 'minor injuries' : _c(255,180,180), 'moderate injuries'  : _c(255,120,120), 'severe injuries' : _c(255,60,60), 'critical injuries' : _c(255,0,0),
          'me3 armor' : _c(241,192,38),
          'armor': _c(241,192,38),           
          }

def shape(shape_name):
    if shape_name not in shapes:
        debug.log("Missing shape: " + shape_name)
    return shapes.get(shape_name, default_shape)

def color(color_name):
    if color_name not in colors:
        debug.log("Missing color: "+color_name)
        return default_color
    return colors[color_name]
