"""
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr "ZasVid" Sikora; see CosmicCommando.py for full notice.
"""

#from guts.game_pieces import Terrain, Feature, Item
#from guts.game_agents import Agent, Player, item_action_types
#from guts.actions import new_action
from guts.debug import debug
from guts.game_quests import Objective, Quest

def prepare_quest(quest_name):
    #board_size = quests[quest_name]["board width x height"] if "board width x height" in quests[quest_name] else SCREEN_WIDTH - HUD_WIDTH, SCREEN_HEIGHT
    quest_outcomes = quests[quest_name]["outcomes"] if "outcomes" in quests[quest_name] else {} 
    acq_message = quests[quest_name]['acquisition message'] if 'acquisition message' in quests[quest_name] else None
    quest = Quest(quest_name, quests[quest_name]["description"], quest_outcomes, quests[quest_name]["status"], acq_message)
    for objective in quests[quest_name]["objectives"]:
        obj_id = objective["id"]
        obj_desc_todo = objective["desc_todo"]
        obj_desc_done = objective["desc_done"]
        obj_kind = objective["kind"]
        obj_target = objective["target"]
        prereqs = objective["prereqs"] if "prereqs" in objective else []
        retroactive = objective["retroactive"] if "retroactive" in objective else True
        """ 
        if "prereqs" in objective:
            for prereq_id in objective["prereqs"]:
                prereqs.append(quest.get_goal(prereq_id))
        """
        repeats = objective["repeats"] if "repeats" in objective else 1
        optional = objective["optional"] if "optional" in objective else False 
        negative = objective["negative"] if "negative" in objective else False
        quest.add_goal(Objective(obj_id, obj_desc_todo, obj_desc_done, obj_kind, obj_target, prereqs, repeats, retroactive, optional, negative))
        
    return quest

quests = {"Huginn": { 
            "description": "Raven Biochemical Labs on Huginn",
            "status": "active",
            "acquisition message": ("From the cockpit of your ship you see Huginn, a small rocky moon with no oxygen. Some of these rocks look " \
                                   "suspicously devoid of spacedust. You are sure that this is just a camouflage for Raven Biochemical Labs. " \
                                   "You prepare your ship to land, getting your sabotage equipment ready.", 'metallic green'),             
            "outcomes" : {"easy": "prepare cybork implants for yourself", "score": "perform careful analysis of cybork implant project"},
            "objectives": [{"id" : "lab sabotage",
                            "desc_todo": "Sabotage lab equipment.",
                            "desc_done": "Raven Biochem Labs on Huginn have been successfully sabotaged.",
                            "kind": "INTERACT",
                            "target": "lab workstation",
                            "repeats": 2
                           }
                          ]
          },
          "Muninn": { 
            "description": "Raven Training Facility, Former Raven Headquarters",
            "status": "active",
            "acquisition message": ("Muninn is a small moon that looks deserted, at least on surface. However, when you lower your spaceship " \
                                   " you can see some old buildings partially hidden in the landscape. Former Raven Headqarters, just like your " \
                                   "capitain said! You prepare your weaponry - you do not expect that getting the data about Lady Raven's whereabouts " \
                                   "will be easy.", 'grave grey'),  
            "outcomes" : {"easy": "hack Raven HQ monitoring system to prepare an assault plan, alerting the terrorists to their system being compromised", \
                          "score": "refrain from hacking Raven HQ system in order to prevent currently planned terrorist acts without risking a change of Raven plans"},
            "objectives": [{"id" : "find data",
                            "desc_todo": "Find a data console to download information on the current location of Raven Headquarters.",
                            "desc_done": "You have downloaded the location of Raven's Nest, the new Raven HQ.",
                            "kind": "INTERACT",
                            "target": "data console"
                           }
                          ]
          },
          "A Murder of Crows": { 
            "description": "Spaceport at Raven staging grounds",
            "status": "active",  
            "acquisition message": ("Raven staging grounds! Numerous spaceship come and go from the spaceport, and your unmarked ship " \
                                   " lands there without problem. Only after seing your cosmic commando suit mechanics and security officers " \
                                   "realize who you are. They rush towards you, ready to attack!", 'omnitool'),
            "outcomes" : {"easy": "use Raven IFF to infiltrate Raven-controlled corporations and steal their military technology", \
                          "score": "use Raven IFF to quickly disarm other dangerous Raven facilities"},
            "objectives": [{"id" : "iff",
                            "desc_todo": "Recover Raven IFF from one of their ships.",
                            "desc_done": "You have a Raven IFF needed to evade Raven's Nest planetary defense systems.",
                            "kind": "INTERACT",
                            "target": "Raven spaceship cockpit"
                           }
                          ]
          },
          "Raven's Nest": { 
            "description": "Raven's Nest, Lady Raven's Secret Base",
            "status": "inactive",
            "acquisition message": ("You enter headquarters of Lady Raven, greeted by silence. You know you are expected. "\
                                   " Lady Raven has for sure concentrated all her forces close to her, getting ready to defend her life, " \
                                   "and her organization, until the very end. Doesn't matter that you have destroyed her labs, her facilities, " \
                                   "her ships and killed her men - while she's alive, the dark heart of terrorism is still beating.", 'player'),
            "outcomes" : {"easy": "join Lady Raven in her quest to make humanity evolve through biotechnology", \
                          "score": "fight Lady Raven to end her reign of terror"},
            "objectives": [{"id" : "find lr",
                            "desc_todo": "Find Lady Raven.",
                            "desc_done": "You have found Lady Raven's command center.",
                            "kind": "SPOT",
                            "target": "Lady Raven"
                           },
                           {"id" : "kill lr",
                            "desc_todo": "Kill Lady Raven.",
                            "desc_done": "You need to defeat Lady Raven.",
                            "kind": "KILL",
                            "target": "Lady Raven",
                            "prereqs": ["find lr"]
                           }
                          ]
          },
          "Asteroid Belt Chase": { 
            "description": "Asteroid Belt Chase",
            "status": "active", 
            "acquisition message": ("You've found and boarded the ship of space pirate captain Bluesteel. " \
                "However, while you were arresting the crew, Bluesteel was launched out of the airlock towards a small getaway ship," \
                " hidden amongst the asteroids. Without hestiation, you jump out into the void, hoping your suits thrusters will let you " \
                "catch up to Bluesteel without smashing into any large rocks.", 'steel blue'),
            "objectives": [{"id" : "catch pirate",
                            "desc_todo": "Catch the space pirate captain Bluesteel.",
                            "desc_done": "You have caught the space pirate captain Bluesteel.",
                            "kind": "USE ON",
                            "target": ("submission net", "Space Pirate Captain Bluesteel")
                           },
                           {"id" : "pirate getaway",
                            "desc_todo": "Don't let the space pirate captain Bluesteel get away.",
                            "desc_done": "You have let the space pirate captain Bluesteel get away.",
                            "kind": "INTERACT",
                            "target": ("Space Pirate Captain Bluesteel", "Blue Raven"),
                            "negative": True,
                           },
                           {"id" : "coscom away",
                            "desc_todo": "Don't drift off too far into the void.",
                            "desc_done": "You have drifted too far into the void.",
                            "kind": "FLAG",
                            "negative": True,
                            "target": "drifted off"
                           }
                          ]
          },
          "Test 1": { 
            "description": "Test Chamber 1",
            "status": "active", 
            "objectives": [{"id" : "kill",
                            "desc_todo": "Kill a cybork.",
                            "desc_done": "You killed a cybork.",
                            "kind": "KILL",
                            "target": "Test Cybork"
                           }
                          ]
          },
          "Test 2": { 
            "description": "Test Chamber 2",
            "status": "active", 
            "objectives": [{"id" : "main",
                            "desc_todo": "Kill a raven officer.",
                            "desc_done": "You killed an officer.",
                            "kind": "KILL",
                            "target": "Raven officer"
                           },
                           {"id" : "opt",
                            "desc_todo": "Kill a raven soldier.",
                            "desc_done": "You killed a soldier.",
                            "kind": "KILL",
                            "optional" : True,
                            "retroactive" : False,
                            "target": "Raven recruit"
                           }
                          ]
          },
          "Test Final": {
            "description": "Test Final Chamber",
            "status": "active", 
            "objectives": [{"id" : "door",
                            "desc_todo": "Defeat the final doorman.",
                            "desc_done": "You're ready to enter the final test chamber.",
                            "kind": "KILL",
                            "target": "Raven doorman"
                           },
                           {"id" : "boss",
                            "desc_todo": "Kill a raven general.",
                            "desc_done": "You killed the final boss.",
                            "prereqs" : ["door"],
                            "kind": "KILL",
                            "target": "Raven general"
                           },
                           {"id" : "minions",
                            "desc_todo": "Kill all raven bodyguards.",
                            "desc_done": "You killed the final bosses' bodyguards.",
                            "prereqs": ["door"],
                            "kind": "KILL",
                            "repeats" : 3,
                            "target": "Raven bodyguard"
                           },
                          ]
          
          }
         }

def prepare_campaign(campaign_title):
    campaign_missions = []
    for mission_title in campaigns[campaign_title]:
        campaign_missions.append(prepare_quest(mission_title))
    return campaign_missions

campaigns = {"Test Commando" : ["Huginn", "Test 1", "Test 2", "Asteroid Belt Chase", "Test Final"],
             "Cosmic Commando" : ["Asteroid Belt Chase", "Huginn", "Muninn", "A Murder of Crows", "Raven's Nest"]
             }
