'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.messages import message, infotip
from guts.game_data import game

def feedback_msg(action, agent):
    #TODO: differentiate between player and other agent's and visibility
    message(*action['msg'])

def flavor(action, agent):
    if agent.is_player():
        if action['touched']:
            message(*action['touched msg'])
        else:
            message(*action['msg'])
            action['touched'] = True
            if 'touched color' in action:
                action.piece.color = action['touched color']
            if 'touched shape' in action:
                action.piece.color = action['touched shape']

def mission(action, agent):
    #TODO: check if objective available
    if (agent.is_player() and not action.piece.flag('npc only')) or (not agent.is_player() and action.piece.flag('npc only')):
        if action['accomplished']:
            message(*action['done msg'])
        else:
            message(*action['msg'])
            game.current_quest.accomplish(action['objective'])
            action['accomplished'] = True
            if 'done color' in action:
                action.piece.color = action['done color']
            if 'done shape' in action:
                action.piece.color = action['done shape']


def replenish(interaction, agent):
    """ Replenish the value of a trait (such as health, shields or ammo) without going over its max value """
    trait, amount = interaction['trait'], interaction['amount']
    if agent[trait] == agent['max ' + trait]:
        if agent.is_player():
            infotip("You're at full " + trait + " already!", trait)
        return False
    else:
        agent[trait] += amount
        if agent[trait] > agent['max ' + trait]:
            agent[trait] = agent['max ' + trait]    
        if agent.is_player():
            message("You replenish your " + trait + " by " + str(amount) + ".", trait)
        else:
            message(agent.name +" replenishes its " + trait + " by " + str(amount) + ".", trait)
        return True

def door_manipulation(interaction, agent):
    """
    """
    piece = interaction.piece
    flags = []
    if piece.flag('closed'):
        for flag in ['blocking', 'blocks sight', 'closed']:
            if piece.flag(flag):
                flags.append(flag)
                piece.unset(flag)
        interaction['flags'] = flags
        interaction['closed shape'] = piece.shape
        piece.shape = interaction['open shape']
        piece.name = piece.name.replace('closed', 'open')
        piece['open'] = True
        if agent.is_player():
            message("You open the {0}.".format(piece.name))
        game.change_visibility_at(piece.x, piece.y) 
    elif piece.flag('open'):
        piece.unset('open')
        piece.name = piece.name.replace('open', 'closed')
        for flag in interaction['flags']:
            piece[flag] = True
        interaction['open shape'] = piece.shape
        piece.shape = interaction['closed shape']
        if agent.is_player():
            message("You close the {0}.".format(piece.name))
        game.change_visibility_at(piece.x, piece.y)
    else:
        raise Exception('Manipulating a door that does not have an open/closed flag.')
        


