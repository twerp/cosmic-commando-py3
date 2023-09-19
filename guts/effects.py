'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

class Effect(object):
    '''
    classdocs
    '''

    def __init__(self, duration):
        '''
        Effect's duration might be a natural number or None.
        Effects with duration == None are permanent.
        Effects with duration 0 are instanteous.
        '''
        self.duration = duration
    
    def initiate(self, piece):
        """ Do things to a piece on initial exposure only.
        """
        pass
    
    def affect(self, piece):
        """ The effects affects a piece during its duration.
        """
        pass
    
    def cease(self, piece):
        """ Do things to a piece when ending.
        """
        pass
    
def cause_effect(effect_name, target, source_data = {}):
    """ Causes an effect to initiate affecting the target.
    """
    pass

effects = {}