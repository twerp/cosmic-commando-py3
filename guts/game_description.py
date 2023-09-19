'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

import guts.grammar as grammar

_trait_levels = { 'shields' : ('shields', {1:'full ', 0.75:'nearly full ', 0.5:'still strong ', 0.25:'weakened ', 0: 'waning '}),
                  'health' : ('injuries', {1:'no ', 0.75:'minor ', 0.5:'moderate ', 0.25:'severe ', 0: 'critical '}),
                }

def trait_level_description(trait, agent):
    current_value = agent[trait]
    max_value = agent["max " + trait]
    trait_ratio = float(current_value)/max_value
    trait_descriptor = _trait_levels[trait][0]
    trait_adjectives = _trait_levels[trait][1]
    if trait_ratio == 1:
        return trait_adjectives[1] + trait_descriptor
    elif trait_ratio > 0.75:
        return trait_adjectives[0.75] + trait_descriptor
    elif trait_ratio > 0.5:
        return trait_adjectives[0.5] + trait_descriptor
    elif trait_ratio > 0.25:
        return trait_adjectives[0.25] + trait_descriptor
    elif trait_ratio > 0.0:
        return trait_adjectives[0] + trait_descriptor
    else:
        return 'no '+ trait
    
def describe_item(item, article = True):
    desc = item.name
    if 'stack' in item and item['stack']!=1:
        desc = "{0}s ({1})".format(item.name, item['stack'])
    elif article:
        desc = grammar.articled(desc)
    if item.flag('primed'):
        desc += ' (primed)'
    if item.flag('heats'):
        if item['heat'] >= item['heat capacity']:
            desc += ' (HOT!)'
    return desc

#TODO: Nightmare Tyrant's ability descriptors, yet unused, but surely adaptable
_trait_desc = {'defense': ['Inferior', 'Competent', 'Superior'],
               'skill': ['Inferior', 'Competent', 'Superior'],
               'attitude' : ['Cautious', '' ,'Reckless'],
               'luck' : ['Unlucky', '' , 'Lucky'],
               'confidence' : ['Stressed', '' ,'Confident']
               }

_duration_description = {
            'permanent': '',
            'temporary': 'temporarily',
            'tactical' : 'tactically'
                    }
    
def duration_description(duration):
    return _duration_description[duration]

def trait_description(trait, trait_level):
    trait_level_mod = 1 if trait_level > 0 else 0 if trait_level == 0 else -1
    descriptor = _trait_desc[trait][1 + trait_level_mod]
    trait_level_magnitude = trait_level * trait_level_mod
    if trait_level_magnitude > 1:
        descriptor += '!'
    if trait_level_magnitude > 2:
        descriptor = descriptor.upper()
    prefix = "{0}: ".format(grammar.capitalise(trait)) if trait in ['defense', 'skill'] else ''
    return prefix + descriptor

     