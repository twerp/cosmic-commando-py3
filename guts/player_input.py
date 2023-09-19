'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''
from collections import defaultdict
from debug import debug

_default_inputs = {
        'escape' : 'QUIT',
        'enter': 'ACCEPT',
        'ctrl up': 'CAMERA NORTH',
        'ctrl down': 'CAMERA SOUTH',
        'ctrl left': 'CAMERA WEST',
        'ctrl right': 'CAMERA EAST',
        'left': 'DIRECTION WEST',
        'right': 'DIRECTION EAST',
        'up': 'DIRECTION NORTH',
        'down': 'DIRECTION SOUTH',
        'z': 'DIRECTION SOUTHWEST',
        'x': 'DIRECTION SOUTH',
        'c': 'DIRECTION SOUTHEAST',
        'a': 'DIRECTION WEST',
        's': 'DIRECTION CENTER',
        'd': 'DIRECTION EAST',
        'q': 'DIRECTION NORTHWEST',
        'w': 'DIRECTION NORTH',
        'e': 'DIRECTION NORTHEAST',
        'keypad 1': 'DIRECTION SOUTHWEST',
        'keypad 2': 'DIRECTION SOUTH',
        'keypad 3': 'DIRECTION SOUTHEAST',
        'keypad 4': 'DIRECTION WEST',
        'keypad 5': 'DIRECTION CENTER',
        'keypad 6': 'DIRECTION EAST',
        'keypad 7': 'DIRECTION NORTHWEST',
        'keypad 8': 'DIRECTION NORTH',
        'keypad 9': 'DIRECTION NORTHEAST',
        'b': 'DIRECTION SOUTHWEST',
        'j': 'DIRECTION SOUTH',
        'n': 'DIRECTION SOUTHEAST',
        'h': 'DIRECTION WEST',
        '.': 'DIRECTION CENTER',
        'l': 'DIRECTION EAST',
        'y': 'DIRECTION NORTHWEST',
        'k': 'DIRECTION NORTH',
        'u': 'DIRECTION NORTHEAST',
        'space': 'INTERACT',
        'm': 'DISPLAY MESSAGES',
        'shift 2': 'DISPLAY CHARACTER INFO',
        'g': 'PICK UP',
        #'p': 'DROP',
        'i': 'INVENTORY',
        'X': 'LOOK',
        'L': 'LEAVE',
        'K': 'DISPLAY KILL LIST',
        'r': 'USE ranged',
        'f': 'USE consumable',
        'v': 'USE deployable',
        't': 'USE activated',
        'tab': 'CYCLE FORWARD',
        'shift tab': 'CYCLE BACKWARD',
        'left click': 'SELECT',
        'right click': 'CANCEL',
        #'1': 'USE power 1',
        #'2': 'USE power 2',
        #'3': 'USE power 3',
        #'4': 'USE power 4',
        #'H': 'HORRENDOUS BUG',
        'V': 'DISPLAY VERSION',
        '?': 'HELP',
        'Q': 'QUEST LOG',
        'ctrl q': 'QUIT',
        'alt f': "DEBUG: CHANGE FOV ALGORITHM",
        'alt s': "DEBUG: SET PLAYER SIGHT",

    }
        
def _keystr(keys):
    if None in keys: 
        return None
    return ' '.join(keys)

class InputManager(object):
    """ Attention: characters that come from pressing shift + one of the special keys 
        (by libtcod's definition) need to be denoted as "shift [special key]". 
        E.g. @ doesn't work, "shift 2" does. Capital letters work properly.
    """
    def __init__(self):
        """
            #TODO: initialize inputs later from a file
        """
        self._inputs = {}
        self._outputs = defaultdict(list)
        self._hardcode_inputs(_default_inputs)
        self.input_provider = None
    
    def add_command(self, keystr, command):
        self._inputs[keystr] = command
        self._outputs[command].append(keystr)

    def command(self, keys):
        return self._inputs.get(_keystr(keys), None) 

    def key_of(self, command, list_all = False):
        return self._outputs[command] if list_all else (self._outputs[command][0] if self._outputs[command] else None)
    
    def _hardcode_inputs(self, inputs):
        for keystr, action in inputs.items():
            self.add_command(keystr, action)

    def get_command(self):
        return self.command(self.input_provider.get_input())
        
    def describe_keybindings(self):
        key_desc = 'Keybindings: \n' \
                                   'Movement: \n' \
                                   '     [q] [w] [e] [a] [d] [z] [x] [c]\n' \
                                   '     numpad digits\n' \
                                   '     vi keys\n' \
                                   '     arrow keys (only orthogonally)\n' \
                                   'Wait: numpad 5 or [s] or [.]\n' \
                                   'Move Camera: ctrl + arrow keys \n' \
                                   'Save & Quit: ESC\n' \
                                   'Close doors: Space\n' \
                                   'Examine/look: [X]\n' \
                                   'Pick up items: [g]\n' \
                                   'Open inventory: [i]\n' \
                                   'Shoot: [r] or LMB on an enemy\n' \
                                   'Set/remove projected shield: [v]\n' \
                                   'Throw equipped grenade: [f]\n' \
                                   'Activate lightning launcher: [tab]\n' \
                                   'Show quest log: [Q]\n' \
                                   'Show message log: [m]\n' \
                                   'Show kill list: [K]\n' \
                                   'Leave a location after completing quest: [L]\n' \
                                   'Show this help: [?]'
        #TODO: automate key help
        return key_desc    
    
input_manager = InputManager()
