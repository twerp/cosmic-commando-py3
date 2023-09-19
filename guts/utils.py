'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.debug import debug
from .libtcodpy import random_get_int
from random import shuffle

def random_int(min_int, max_int):
    return random_get_int(0, min_int, max_int)

def random_pos(max_int):
    return random_get_int(0, 1, max_int)

def random_nat(max_int):
    return random_get_int(0, 0, max_int)

def coinflip():
    return (random_int(0, 1) == 1)

def roll_dice(dice = 1, sides = 10):
    value = 0
    for _ in range(dice):
        value += random_pos(sides)
    return value 

def random_permutation(elements):
    shuffle(elements)
    return elements

def random_combination(elements, combination_size):
    if combination_size > len(elements):
        debug.log("Combination of size: " + str(combination_size) + " called for a list of " + str(len(elements)) + " elements.")
    result = []
    mutable_elements = []
    mutable_elements.extend(elements)
    for _ in range(combination_size):
        result.append(mutable_elements.pop(random_nat(len(mutable_elements) - 1)))
    return result

def random_multicombination(elements, multicombination_size):
    if len(elements)<= 0:
        debug.log("choosing a random multicombination from an empty list of elements.")
    result = []
    for _ in range(multicombination_size):
        result.append(elements[random_nat(len(elements) - 1)])
    return result

def random_choice(elements):
    return elements[random_nat(len(elements) - 1)]

def random_weighted_choice(chances_dict):
    weights = list(chances_dict.values())
    names = list(chances_dict.keys())
    total_weight = sum(weights)
    assert total_weight > 0, "Can't return random choice: all chances are 0."
    #the dice will land on some number between 1 and the total weight
    dice = random_int(1, total_weight)
    #go through all weights, keeping the total so far
    running_sum = 0
    choice = 0
    for w in weights:
        running_sum += w
        #see if the dice landed between the total weight of this choice and the next one
        if dice <= running_sum:
            return names[choice]
        choice += 1

eight_directions = [(-1,-1), (0,-1), (1,-1), (0,1), (1,1), (1,0), (-1,1), (-1,0)]
compass_directions = ["NW","N","NE","E","SE","S","SW","W"]
cardinal_directions = ["N", "E", "S", "W"]
directions = {"west" : (-1,0), "east" : (1,0), "north" : (0,-1), "south" : (0,1), "center" : (0,0),
              "northwest" : (-1,-1), "northeast" : (1,-1), "southwest" : (-1,1), "southeast" : (1,1),
              "WEST" : (-1,0), "EAST" : (1,0), "NORTH" : (0,-1), "SOUTH" : (0,1), "CENTER" : (0,0),
              "NORTHWEST" : (-1,-1), "NORTHEAST" : (1,-1), "SOUTHWEST" : (-1,1), "SOUTHEAST" : (1,1),
              4 : (-1,0), 6 : (1,0), 8 : (0,-1), 2 : (0,1), 7 : (-1,-1), 9 : (1,-1), 1 : (-1,1), 3 : (1,1), 5 : (0,0),
              "W" : (-1,0), "E" : (1,0), "N" : (0,-1), "S" : (0,1), "NW" : (-1,-1), "NE" : (1,-1), "SW" : (-1,1), "SE" : (1,1), "C" : (0,0),
              "full names" : {(-1,-1) : "NORTHWEST", (0,-1) : "NORTH", (1,-1) : "NORTHEAST", (0,1) : "EAST",
                              (1,1): "SOUTHEAST", (1,0): "SOUTH", (-1,1): "SOUTHWEST", (-1,0): "WEST",
                              (0,0) : "CENTER" },
              "initials" : {(-1,-1) : "NW", (0,-1) : "N", (1,-1) : "NE", (0,1) : "E",
                              (1,1): "SE", (1,0): "S", (-1,1): "SW", (-1,0): "W",
                              (0,0) : "C" } 
              }

def orientation(direction):
    if isinstance(direction, str):
        diagonal = len(direction) == 2 or len(direction) > 6 
    else:
        diagonal = abs(direction[0]) + abs(direction[1]) == 2
    return 'diagonal' if diagonal else 'orthogonal'