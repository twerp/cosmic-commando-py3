'''
This code is part of NightmareTyrant; Copyright (C) 2013 Piotr 'ZasVid' Sikora; see NightmareTyrant.py for full notice.
'''

from .utils import random_nat
from collections import defaultdict

traits = ['health', 'stamina', 'special equipment', 'defense', 'skill', 'attitude', 'luck',  'confidence']
trait_losses = { 'damage' : 'health',
                  'fatigue' : 'stamina',
                  'caution' : 'attitude',
                  'jinx' : 'luck',
                  'imbalance': 'defense',
                  'stress': 'confidence' ,
                  'disability' : 'skill',
                  'loss of items' : 'special equipment'
                 }
trait_gains = { 'health' : 'damage',
                 'stamina' : 'fatigue',
                 'attitude' : 'caution',
                  'luck': 'jinx',
                  'defense': 'imbalance',
                  'confidence': 'stress',
                  'skill': 'disability' ,
                  'special equipment':'loss of items' 
                 }

trait_mods = ['temporary', 'tactical']

"""
Dice tables return (successes, advantages)
"""
dice_tables = {'attitude' : 
               {
               -6: (1,  1),
               -5: (1,  1),
               -4: (1, -1),
               -3: (1, -1),
               -2: (1,  1),
               -1: (1,  1),
                0: (1,  0),
                1: (1,  0),
                2: (0,  0),
                3: (0,  0),
                4: (1,  0),
                5: (1,  0),
                6: (0, -1),
                7: (0, -1),
                8: (1,  0),
                9: (1,  0),
               10: (1,  0),
               11: (2, -1),
               12: (0,  1),
               13: (0,  1),
               14: (1, -1),
               15: (2, -1)
               },
               
               'ability' : 
               {
               -6: (0,  0),
               -5: (0,  0),
               -4: (0,  1),
               -3: (0,  1),
               -2: (1,  0),
               -1: (1,  0),
                0: (0,  0),
                1: (0,  0),
                2: (0,  0),
                3: (0,  0),
                4: (0,  0),
                5: (0,  1),
                6: (1,  0),
                7: (1,  0),
                8: (1,  1),
                9: (1,  1),
               10: (0,  1),
               11: (0,  1),
               12: (0,  0),
               13: (1,  0),
               14: (0,  1),
               15: (2,  0)
               },
               
               'luck' : 
               {
               -6: (-1, 0),
               -5: (0, -2),
               -4: (0, -2),
               -3: (1,  0),
               -2: (0, -1),
               -1: (0, -1),
                0: (0,  0),
                1: (0,  0),
                2: (0, -1),
                3: (0, -1),
                4: (0,  0),
                5: (0,  0),
                6: (0,  1),
                7: (0,  1),
                8: (0,  0),
                9: (0,  0),
               10: (0,  1),
               11: (0,  1),
               12: (0, -1),
               13: (0,  2),
               14: (0,  2),
               15: (1,  0)
               },
               
               'resistance' : 
               {
               -6: (-2,  0),
               -5: (-1, -1),
               -4: (0, -1),
               -3: (0, -1),
               -2: (-1,  0),
               -1: (0, -1),
                0: (0, -1),
                1: (0, -1),
                2: (0,  0),
                3: (0,  0),
                4: (-1, 0),
                5: (0, -1),
                6: (0,  0),
                7: (0,  0),
                8: (0, -1),
                9: (0, -1),
               10: (0,  0),
               11: (0,  0),
               12: (0,  1),
               13: (0,  1),
               14: (0, -1),
               15: (0, -1)
               },
}

def resolve_task(attitude, ability, luck, resistance):
    successes = 0
    advantages = 0
    
    die_mods = {
            'attitude' : attitude * 2,
            'ability' : ability * 2,
            'luck' : luck * 2,
            'resistance' : resistance * 2
            }
    for die_type in list(dice_tables.keys()):
        die_roll = random_nat(9) + die_mods[die_type]
        successes += dice_tables[die_type][die_roll][0]
        advantages += dice_tables[die_type][die_roll][1]
    return (successes, advantages)


"""
if __name__ == '__main__':
    results = defaultdict(int)
    for attitude in range(-3,4):
        for ability in range(-3,4):
            for luck in range(-3,4):
                for resistance in range(-3,4):
                    suc, adv = resolve_task(attitude, ability, luck, resistance)
                    res = ""
                    if adv > 0:
                        res += "Advantageous"
                        if adv > 1:
                            res = str.upper()
                        if adv > 2:
                            res += "!" * (adv -2)
                    elif adv < 0:
                        res += "Miserable"
                        if adv < -1:
                            res = str.upper()
                        if adv < -2:
                            res += "!" * (adv -2)
                    if suc > 0:
                        res += "Success" + "!" * suc
                    else:
                        if suc < 0:
                            res += "Critical"
                        res += "Failure"
                    results["Sux " + str(suc)] += 1
                    results["Advs " + str(adv)] += 1    
                    print(res)
    print (results)
"""     
    