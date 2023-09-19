'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from config import MSG_WIDTH
from game_data import game
import textwrap
import guts.grammar as grammar

#TODO: consider adding agent messages, differentiating between player and non-players
# {instead of having to do in every place an agent does something}

#TODO: consider differentiating between messages from the log and inconsequential interface/environment tips
#e.g. bumping into walls, 

#TODO: consider adding delayed messages:
"""
    def add_delayed(self,message):
         Capable of adding a delayed messages, which gets flushed when a normal message is added.
            Further delayed messages and 
        if self.delayed_message is None:
            self.delayed_message = message
        else:
            self.delayed_message += message 
            
    def add(self,message):
        if self.delayed_message is not None:
            message = self.delayed_message + message
            self.delayed_message = None
        """
    
def infotip(new_tip, color = 'white'):
    game.add_infotip(grammar.capitalise(new_tip), color)    
    
def message(new_msg, color = 'white'):
    msg = grammar.capitalise(new_msg)
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap( msg, MSG_WIDTH)
    game.msg_archive.append( (msg, color) )
    for line in new_msg_lines:
        #add the new line as a tuple, with the text and the color
        game.msgs.append( (line, color) )
        
