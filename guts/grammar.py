'''
Created on Aug 5, 2013

@author: zasvid
'''

def a_or_an(word):
    return 'an' if word[0] in ['a', 'i', 'o', 'u', 'e'] else 'a'
    
def articled(word):
    return a_or_an(word) + ' ' + word    

def capitalise(string):
    return string[0].upper() + string[1:] if string != '' else '' 
    
def possessive(agent):
    s = str(agent.name)
    if agent.is_player():
        s += 'r'
    else:
        s+= "'"
        s += '' if agent.name[-1] == 's' else 's'
    return s 

def possessive_pronoun(agent):
    return 'your' if agent.is_player() else 'their'

def conjugate(verb, agent):
    s = verb
    if not agent.is_player():
        if verb[-1] == 's':
            s += 'e'
        s += 's'
    return s 