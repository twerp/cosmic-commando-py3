'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

import os
from . import libtcodpy as libtcod
from guts.messages import message, infotip
import guts.grammar as grammar
from guts.debug import debug
from guts.game_data import game
from guts.game_piece_defs import new_player, new_item
from guts.board_generation import generate_board
from guts.config import INFO_WIDTH, GAME_ACTION_TIMEOUT, GAME_VERSION, AUTHOR_EMAIL, GameSettings
from guts.utils import compass_directions, directions, coinflip
from guts.player_input import input_manager
from guts.actions.combat import closest_agent
from guts.game_quests import Quest, Objective
from guts.game_goals_defs import prepare_quest, prepare_campaign
from guts.geometry import Line, distance, Point
from guts.game_description import describe_item
from guts.libtcod_tables import fov_algorithms

class GamePlay(object):
    '''
    This class handles playing the game.
    '''

    def __init__(self, ui, achievements):
        self.ui = ui
        self.achievements = achievements
        self.savefile = 'savegame'
        self.previous_target = None
        input_manager.input_provider = ui

    def new(self, time_limit = False):
        """ New game is the place to setup everything for a new game to start, including:
            * reset of game data to default values 
            * ask the player for input for initialisation variables (e.g., character creation)
             
        """
        self.ui.clear()
        self.intro_screen()
        game.new(time_limit)
        game.state = 'briefing'
        #create object representing the player
        game.player = new_player()
        game.quests = prepare_campaign('Test Commando' if debug.test else 'Cosmic Commando')
    
    def intro_screen(self):
        self.ui.msgbox("You're here, good!\nWe need to discuss your mission before you depart." \
                       "We've received information that Ravens, the most dangerous terrorist group in the galaxy," \
                       " led by Lady Raven, self-proclaimed Queen of Darkness, are preparing an operation to overthrow our government. " \
                       "We must act before it's too late.\n\nLady Raven thinks she's smart, but we are smarter. " \
                       "Our intelligence has learned that on a moon called Huginn there is a secret lab where " \
                       "she produces cybernetic soldiers to use in the attack. You must go there and sabotage their lab equipment. " \
                       "Otherwise our military will not be able to stop Raven forces if they attack.\n\n" \
                       "Speaking of intelligence... The infamous Space Pirate Captain Bluesteel's hideout is supposedly in an asteroid " \
                       "belt nearby. We sure could use the enormous bounty on Bluesteel to better protect the government from terrorists. " \
                       "If you find some spare free time, make sure to capture the pirate alive! \n\n" \
                       "Ekhm, getting back to official business: Your main objective is to find and kill Lady Raven. " 
                       " Without her, the organization will fall apart, for it is her charm and wit that holds all the terrorists together. " \
                       "However, we do not know where is her secret lair. You may find the directions to it on Muninn, " \
                       "in the former Raven headquarters. We suspect that Lady Raven's hideout is heavily guarded, " \
                       "so you should also first acquire Raven IFF to get past any anti-ship defence undetected. \n\n" \
                       "We have given you all resources that we have and " \
                       "you're authorized to use any means necessary to get the job done. Good luck, do not let us down! "
                       , 'warning')
    
    def test(self):
        self.new()
        item = new_item('debug launcher')
        game.player.receive(item)
        game.player.equip(item)
        choice_keys = ['Huginn','Muninn','A Murder of Crows']
        for choice in choice_keys:
            game.choices[choice] = coinflip() or True
        [quest for quest in game.quests if quest.is_inactive()][0].status = 'active'
        message("Choices for this game are: {0}.".format(', '.join(["{0}:{1}". \
                format(choice, game.choices[choice]) for choice in choice_keys])),'gold')
    
    def load(self, savefile):
        self.ui.clear()
        game.load(savefile)
        
    def text_play(self):
        #display quests to choose from
        self.ui.clear()
        quit_game = False
        """ Debriefing stage """
        if game.state == 'debriefing':
            if game.current_quest.name.find("Aster") >=0:
                #TODO: deal with player's sight in another way. perhaps by some parameter of location for obscured and unobscured vision
                game.player['sight'] = 8
                game.player['velocity'] = (0,0)
                subnet = None
                powerfist = None
                for item in game.player.inventory:
                    if item.name == 'submission net':
                        subnet = item
                    elif item.name == 'power fist':
                        powerfist = item
                game.player.equip(powerfist, silently = True)                    
                game.player.inventory.remove(subnet)
                message("Submission net won't be useful in further missions.", 'submission')
            while game.current_quest.is_completed() and game.current_quest.outcomes != {}:
                decision = self.ui.menu('Decide the outcome of you completing the mission "{0}":'.format(game.current_quest.name),
                                    [('{0} (makes final mission [e]asier)'.format(game.current_quest.outcomes['easy']), 'e', 'player'),
                                     ('{0} (increases final mission [s]core)'.format(game.current_quest.outcomes['score']), 's', 'gold')],
                                    indexing = self.ui.MENU_NUMCOMBO_INDEX)
                if decision is not None:
                    game.choices[game.current_quest.name] = decision == 0
                    message("You have chosen to {0}.".format(game.current_quest.outcomes['easy' if decision == 0 else 'score']), 'player' if decision == 0 else 'gold')
                    break
            if len([quest for quest in game.quests if quest.is_completed() and quest.name.find("Aster") < 0]) >= 3:
                [quest for quest in game.quests if quest.name == "Raven's Nest"][0].status = 'active'
            game.player['shield recharge'] = game.player['max shields']
            game.player['health'] = game.player['max health']
            for item in game.player.inventory:
                if item.flag('heats'):
                    item['heat'] = 0
                if item.flag('stacks'):
                    item['stack'] = 8  
            game.player.recharge()
        game.state = 'briefing'
        self.ui.clear()
        self.ui.render_hud()
                                        
        """ Briefing stage - choosing next quest """
        quest_choices = []
        quest_choices.append(('Save & Quit [S]', 'S'))
        custom_index = ord('a')
        for quest in [quest for quest in game.quests if not quest.is_inactive()]:
            quest_choices.append(("{0} {2}{1}{3}".format( quest.name, 
                                     chr(custom_index) if quest.is_active() else 'completed' if quest.is_completed() else 'failed',
                                    '(' if not quest.is_active() else '[',
                                    ')' if not quest.is_active() else ']',
                                    ), chr(custom_index), quest.name if quest.is_active() else 'completed quest' if quest.is_completed() else 'failure'))
            custom_index += 1
        
        while True:
            chosen_quest_index = self.ui.menu('Select your destination: ',
                                    quest_choices, indexing = self.ui.MENU_NUMCOMBO_INDEX)
            if chosen_quest_index is not None:
                chosen_quest_index -= 1 # 
                if chosen_quest_index < 0: #>= len(game.quests): # save & quit
                    game.save(self.savefile)
                    quit_game = True
                    break
                chosen_quest = game.quests[chosen_quest_index]
                if chosen_quest.is_finished():
                    self.ui.msgbox("This quest has been already {0}!".format(
                            'failed' if chosen_quest.is_failed() else 'completed'),
                        'failure' if chosen_quest.is_failed() else 'completed quest')
                else: #quest properly chosen, can proceed to board game part
                    break
        #generate map (at this point it's not drawn to the screen)
        if not quit_game:
            game.current_quest = chosen_quest
            if game.current_quest.name == 'Muninn':
                height, width = (64, 64)
            elif game.current_quest.name == "Raven's Nest":     
                height, width = (75, 75)
            elif game.current_quest.name == "Asteroid Belt Chase":
                height, width = (44, 250)
                subnet = new_item("submission net")
                game.player.receive(subnet)
                game.player.equip(subnet)
            else:
                height, width = (44, 44)
            game.board = generate_board(width, height, player = game.player, mission = chosen_quest.name)
            #TODO: hack for final mission preparations
            if game.current_quest.name == "Raven's Nest":
                if game.kill_list['Raven officer'] > 0:
                    item = new_item('ravenous rapier')
                    game.player.receive(item)
                    message("You have recovered a ravenous rapier from one of the Raven officers and we made it work for you!", item.color)
                if game.choices['Huginn']:
                    game.player['armor'] = 5
                    message("Your new cybork implants will reduce the amount of damage you'll take from enemy attacks.", 'armor')
                if game.choices['Muninn']:
                    message("The maps made after hacking Raven's Nest monitoring systems have proven accurate.", 'light watery')
                    for tile in game.board.tiles:
                        tile.explored = True
                        tile._remembered_shape = tile._main_piece().shape
                if game.choices['A Murder of Crows']:
                    message("Raiding Raven-affiliated weapon manufacturers paid off with a handful of EMP grenades. Use on highly shielded targets.", 'stunning blue')
                    for _ in range(4):
                        game.player.receive(new_item("EMP grenade"))
            if game.current_quest.acquisition_message is not None:
                message(*game.current_quest.acquisition_message)
        return quit_game
        
    def show_gfx(self):
        if game.state == 'show gfx':
            infotip("Press any command key to stop watching the fireworks!")
            self.ui.render_hud()
            self.ui.render_gfx()
            libtcod.console_flush()
            
            player_input = None
            timeout_start = libtcod.sys_elapsed_seconds()
            while player_input is None and (not game.is_time_limited() or libtcod.sys_elapsed_seconds() <= GAME_ACTION_TIMEOUT + timeout_start):
                player_input = input_manager.get_command()
            game.state = game.previous_state
            game.previous_state = None
            
    def board_play(self):
        quit_game = False
        finish_tactical_play = False
        game.initialize_vision()
        turns_taken = 0
        center_on_player = True
        self.refresh = True
        game.state = 'playing'
        infotip("Press the [?] key to view help.")
        infotip(str(game.board[game.player.x, game.player.y])[5:])
        while not quit_game and not finish_tactical_play:
            #render the screen
            if self.refresh:
                if game.current_quest.is_finished():
                    if game.current_quest.is_failed():
                        infotip("You failed your current quest! You can now leave by pressing [L] if there are no opponents in sight.", 'failure')
                    else:
                        infotip("Your current quest is completed! You can leave by pressing [L] if there are no opponents in sight.", 'completed quest')
                self.ui.render_all(center_on_player)
                self.refresh = False
            else:
                self.ui.render_mouseover_info()
            libtcod.console_flush()
                
            if turns_taken == 0 or game.state != 'playing':
                turns_taken, quit_game, center_on_player = self.player_action(center_on_player)
            for _ in range(turns_taken):
                game.player.recharge()
            self.show_gfx()
            if game.current_quest is not None:
                game.current_quest.progress_objectives()
                #TODO: hack for final decision
                if game.current_quest.name == "Raven's Nest" and game.current_quest.get_goal('find lr').is_fulfilled() and "Raven's Nest" not in game.choices:
                    self.ui.msgbox("You have found Lady Raven! You are mere moments away from your mission being finally at end. Proceed carefully. " \
                                       "\nPress <Escape>, <Space> or <Enter> to proceed.", hard_lock = True)
                    speech = ["So you've come here, a foolish pawn of the so-called Humanity Protectorate. " \
                                  "Your masters are doing the very opposite of protecting the humanity, holding it back by clinging to nature's imperfect designs. ",
                                  "Now that you're here and they cannot shield you from my message, as they do with the masses out there, you can listen and wake up. " \
                                  "Humanity one day will make contact with alien life. It might be hostile and it might be dangerous. We must be prepared and capable, " \
                                  "and your government's ideology is an obstacle in that process, a barrier to learning and growth. It must be removed.\n\n" \
                                  "Join me and give humanity hope to survive. Fight me and doom the species to be victims in the natural struggle of galactic life!"
                             ]
                    for speechbox in speech:
                        self.ui.render_all(center_on_player)
                        self.ui.msgbox(speechbox, default_text_color = 'maroon')
                        message(speechbox, 'maroon')
                    while game.current_quest.name not in game.choices:
                        self.ui.render_all(center_on_player)
                        decision = self.ui.menu('Time to make your decision!',
                            [('{0} (game ends)'.format(game.current_quest.outcomes['easy']), 'e', 'player'),
                            ('{0} (game proceeds to the boss fight, increased score)'.format(game.current_quest.outcomes['score']), 's', 'gold')],
                            indexing = self.ui.MENU_NUMCOMBO_INDEX, default_text_color = 'maroon')
                        print(decision)
                        if decision is not None:
                            end_game = decision == 0
                            game.choices[game.current_quest.name] = end_game
                            message("You have chosen to {0}.".format(game.current_quest.outcomes['easy' if end_game else 'score']), 'player' if end_game else 'gold')
                            if end_game:
                                infotip("Press <Escape> to return to main menu.", 'gold')
                                self.ui.render_all(center_on_player)
                                self.ui.msgbox("Congratulations! You've joined the Raven Wings and enhanced the humanity's chance to become the supreme species of the galaxy! Press any key to return to main menu.", default_text_color = 'gold')
                                game.state = 'victory'
                                quit_game = True
                    self.ui.render_all(center_on_player)

                if game.current_quest.is_completed() and game.current_quest == game.quests[-1] and not game.state.startswith('victory'): #TODO: do something better than game.quests[-1]
                    congratulatory_message = "Congratulations! You have saved the Humanity Protectorate from terrorists!" 
                    message(congratulatory_message, 'gold')
                    infotip("Press <Escape> to return to main menu.", 'gold')
                    game.state = 'victory'
                    self.ui.render_all(center_on_player)
                    self.ui.msgbox(congratulatory_message, default_text_color = 'gold')
                    quit_game = True
            if game.state == 'debriefing':
                finish_tactical_play = True
            if game.state == 'playing' and turns_taken > 0:
                game.fov_check()
                """
                if game.agents_in_sight == [game.player]:
                     Tactical refresh - check if an encounter is over (no opponent in sight) and remove all tactical effects,
                        both from player character and their opponents. 
                              
                    if game.player.refresh(full = False):
                        message("Without anything threatening you, you can catch your breath, readjust your outfit, " \
                                " reload your crossbow and you're ready for another fight!", 'positive')
                                  
                    pass
                    """    
                infotip(str(game.board[game.player.x, game.player.y])[5:])                
                turns_taken -= 1
                for agent in game.agents:
                    if agent != game.player and agent['ai'] is not None:
                        agent.recharge()
                        agent.act()
                        if game.state == 'dead':
                            break
                self.show_gfx()
                for agent in game.agents:
                    agent.apply_velocity()
            if quit_game:
                if game.state in ['dead','victory']:
                    quests_completed = sum([1 for quest in game.quests if quest.is_completed()])
                    score = quests_completed
                    if quests_completed >= 3:
                        for choice in list(game.choices.keys()):
                            if choice != "Raven's Nest" and not game.choices[choice]:
                                score += 1
                        if game.state == 'victory':
                            score += 3
                            if not game.choices["Raven's Nest"]:
                                score += 4
                    if game.is_time_limited():
                        score *= 2
                    self.achievements.add_highscore(score)
                    self.ui.render_all(center_on_player)
                    self.ui.msgbox("Your score: {0}/30".format(score), default_text_color = 'gold')
                    self.achievements.remember(game)
                    #TODO: os.remove(self.savefile) # enable to disable savescumming. Possibly make a debug option
                    game.state = 'finished'
                #else:
                #    game.save(self.savefile)
        return quit_game
    
    def play(self):
        self.prepare_play()
        quit_game = False
        while not libtcod.console_is_window_closed():
            if game.state.find('briefing') >= 0:
                quit_game = self.text_play()
            if not quit_game:
                quit_game = self.board_play() or game.state == 'victory'
            if quit_game:
                break
            
        if game.state != 'finished':
            infotip("Saving game...", 'electric')
            self.ui.render_hud()
            libtcod.console_flush()
            game.save(self.savefile)

    def select_adjacent_tile(self, unblocked_only = False):
        """return a tile next to the player selected by a direction key
            or None if escaped
        """
        while True:
            infotip('Select a direction ([qweadzxc] or Numpad [12346789]) or press' \
                '<Esc>, <Space>, or Right Click to cancel.'.format())
            self.ui.render_hud()
            libtcod.console_flush()
            player_action = input_manager.get_command()
            if player_action is not None and player_action.startswith('DIRECTION '):
                dx, dy = directions[player_action[10:]]
                #the coordinates the player is moving to/attacking
                x = game.player.x + dx
                y = game.player.y + dy
                if not game.board.contains_position(x,y):
                    infotip("There's nothing relevant in that direction!", 'warning')
                elif unblocked_only and game.board[x,y].is_blocked(): 
                    infotip("That direction is blocked.")
                else:
                    return game.board[x,y] 
            elif player_action in ['CANCEL', 'QUIT']:
                return None

    def select_target_tile(self, occupied = False, exclude_player = True, max_range = None, visible = True, clear_line = True, confirm_action = None):
        """ Return a tile selected by the player via left click or maneuvering with a selecting line, 
            respecting the parameters of required choice (whether the tile has to be occupied, can it be the player's tile,
            whether it needs to be in given max range from the player, whether it needs to be in player's FOV,
            whether there must be an unblocked line from the player to the selected tile.
            
            If the selected tile doesn't satisfy the constraints, an infotip is posted and the process of selection continues.
             
            The method will return None the selection is cancelled.
        """
        def compute_constraints(tile):
            constraint = {}
            constraint['visibility'] = not visible or tile.visible
            constraint['range'] = max_range is None or distance(game.player, tile) <= max_range
            constraint['occupied'] = not occupied or tile.occupant is not None
            constraint['player'] = True if tile.occupant is None else (not exclude_player or not tile.occupant.is_player())
            return constraint  
        agents_in_range = sorted([agent \
                                   for agent in game.agents \
                                   if (max_range is None or distance(game.player, agent) <= max_range) \
                                        and (not visible or game.board[agent.x, agent.y].visible) \
                                        and (not clear_line or not Line(game.player, agent).is_blocked()) \
                                        and (not agent == game.player) \
                                   ], key = lambda agent: distance(game.player, agent)) 
        if self.previous_target is not None:
            default_target = self.previous_target
            if default_target.x is None:
                self.previous_target = None
            else:
                if not all(compute_constraints(game.board[default_target.x, default_target.y]).values()):
                    self.previous_target = None
        if self.previous_target is None:
            default_target = agents_in_range[0] if agents_in_range else game.player 
        target = Point(default_target.x, default_target.y) if default_target is not None else Point(game.player.x, game.player.y)
        finished_selecting = False
        update_display = True
        while not finished_selecting:
            #TODO: refresh stuff under mouse and hud
            if update_display:
                infotip('<left click> on a{0} to select a target\n' \
                        '<{1}> or <{2}> confirm current selection\n' \
                        '<movement keys> move selection cursor\n' \
                        '<{6}>, <{7}> cycle target selection\n' \
                        '<{3}>, <{4}>, or <{5}> cancel.'.format('n enemy' if occupied else ' tile', input_manager.key_of(confirm_action),
                input_manager.key_of("ACCEPT"), input_manager.key_of("INTERACT"), input_manager.key_of("QUIT"), input_manager.key_of("CANCEL"),
                input_manager.key_of("CYCLE FORWARD"), input_manager.key_of("CYCLE BACKWARD")))

                infotip(str(game.board[target.x, target.y]))
                self.ui.render_hud()
                line = Line(game.player, target)
                self.ui.render_targeting(line)
                libtcod.console_flush()
            update_display = True
            player_action = input_manager.get_command()
            tile = self.ui.get_tile_under_mouse()
            if (player_action == 'SELECT' and tile is not None) or (confirm_action is not None and player_action in [confirm_action, 'ACCEPT']):
                if player_action != 'SELECT' and line.is_blocked() and clear_line:
                    target = line.blocking_point
                    infotip("Your aim is blocked! Target reset to blocking tile.")
                elif player_action == 'SELECT':
                    target = tile
                tile = game.board[target.x, target.y]
                constraints = compute_constraints(tile)                    
                if all(constraints.values()):
                    finished_selecting = True
                elif not constraints['visibility']:
                    infotip("Target must be visible!")
                elif not constraints['range']:
                    infotip("Target outside range of {0} tiles.".format(max_range))
                elif not constraints['occupied']:
                    infotip("Target must be a combatant!")
                elif not constraints['player']:
                    infotip("You can't target yourself!")
            elif player_action is not None and player_action.startswith('DIRECTION '):
                dx, dy = directions[player_action[10:]]
                p = Point(target.x + dx, target.y + dy)
                if game.board.contains_position(p.x,p.y):
                    target = p
            elif player_action is not None and player_action.startswith('CYCLE '):
                forward = player_action == 'CYCLE FORWARD'
                min_distance = game.board.width * game.board.height + 1
                min_agent = None
                if target is None:
                    target = agents_in_range[0] if agents_in_range else game.player
                elif agents_in_range:
                    target_cycle = agents_in_range if forward else agents_in_range[::-1] 
                    for agent in target_cycle + [target_cycle[0]]:
                        if min_distance == 0:
                            min_agent = agent
                            break
                        if distance(target, agent) < min_distance:
                            min_distance = distance(target, agent)
                            min_agent = agent
                if min_agent is None:
                    infotip("No targets available to cycle through!")
                else:
                    target = min_agent
            elif player_action in ['CANCEL', 'QUIT', 'INTERACT']:
                target = None
                finished_selecting = True
            else:
                update_display = False
        self.ui.wipe_targeting()    
        if target is not None:
            target = game.board[target.x, target.y].occupant if occupied else game.board[target.x, target.y]
            self.previous_target = target 
            return target
        else:
            return None

            
    def player_action(self, old_center_on_player):
        """ Returns how many turns passed, whether the player has quit
            and whether the camera should center on player.
            
            @return turns taken, quit game, center camera on player
            
            #TODO: consider a dictionary of player action outcomes.
            #TODO: consider returning the amount of turns an action would take (NEW: eh? don't we do it already?)
        """
        center_on_player = old_center_on_player
        turns_taken = 0
        quit_game = False
        
        if game.is_time_limited() and game.state == 'playing':
            player_action = None
            timeout_start = libtcod.sys_elapsed_seconds()
            while libtcod.sys_elapsed_seconds() <= GAME_ACTION_TIMEOUT + timeout_start and player_action is None:
                player_action = input_manager.get_command()
            #print(libtcod.sys_elapsed_seconds(), GAME_ACTION_TIMEOUT + timeout_start, player_action, game.state)
            if libtcod.sys_get_last_frame_length() > GAME_ACTION_TIMEOUT and player_action is None and game.state == 'playing':
                message("You wait.")
                self.refresh = True
                turns_taken = 1
        else:
            player_action = input_manager.get_command()
        if player_action is not None:
            self.refresh = True
            player = game.player
            center_on_player = True
            if player_action.startswith("DEBUG:") and debug.active:
                if player_action == 'DEBUG: CHANGE FOV ALGORITHM':
                    choices = list(fov_algorithms.keys())
                    index = self.ui.menu('Select fov algorithm:', choices)
                    if index is not None:
                        GameSettings.FOV_ALGO = fov_algorithms[choices[index]]
                        infotip("FOV Algorithm in use: {0} - number {1}.".format(choices[index], GameSettings.FOV_ALGO)) 
                        game.fov_recompute = True
                        game.fov_check()
                elif player_action == 'DEBUG: SET PLAYER SIGHT':
                    #TODO: menus must return underlying objects, not just indexes
                    allowed_sights = ['2','4','8','16','100']
                    index = self.ui.menu('Select sight range:', allowed_sights)
                    if index is not None:
                        game.player['sight'] = int(allowed_sights[index])
                        game.fov_recompute = True
                        game.fov_check()
            elif player_action == 'DISPLAY MESSAGES':
                self.ui.listbox('Message log:', game.msg_archive, width = INFO_WIDTH, scroll_to_bottom = True)
            elif player_action == 'DISPLAY VERSION':
                infotip('Version: {0}'.format(GAME_VERSION), 'ui text')
            elif player_action == 'DISPLAY KILL LIST':
                kill_list = []
                for kill, killcount in list(game.kill_list.items()):
                    if killcount > 0:
                        kill_list.append("{0} {1}{2}".format(killcount, kill, 's' if killcount > 1 else ''))
                self.ui.listbox('Kill list:', kill_list, width = INFO_WIDTH)
            elif game.state == 'playing':
                if player_action.startswith('CAMERA '):
                    dx, dy = directions[player_action[7:]]
                    self.ui.move_camera(dx * 10, dy * 10)
                    center_on_player = False
                elif player_action == 'DISPLAY CHARACTER INFO':
                    self.ui.msgbox('TODO: Display character info.')
                elif player_action == 'HELP':
                    self.ui.msgbox(input_manager.describe_keybindings())
                elif player_action == 'QUEST LOG':
                    objective_list = []
                    for objective in list(game.current_quest.objectives.values()):
                        objective_text = objective.description
                        objective_text += '.' if objective.repeats == 1 else ': {0}/{1}'.format(objective.accomplished, objective.repeats)
                        objective_color = 'objective '+ objective.status
                        if debug.info or objective.is_available():
                            objective_list.append((objective_text, objective_color))
                    self.ui.listbox(game.current_quest.name, objective_list)
                elif player_action == 'QUIT':
                    if 0 == self.ui.menu("Save and quit to main menu?", [('[Y]es, save & quit.', 'y', 'player'), ('No (default response).', 'n', 'gold')], indexing = self.ui.MENU_CUSTOM_INDEX):
                        quit_game = True
                elif player_action.startswith('DIRECTION '):
                    turns_taken = 1 if self.player_act_in_direction(directions[player_action[10:]]) else 0
                elif player_action.startswith('CYCLE'):
                    pass #TODO: weapon cycling 
                elif player_action == 'INTERACT':
                    """ This allows to interact with features that can't be bumped into.
                    """
                    traversible_features = []
                    x,y = player.x, player.y
                    for tile in game.board.ring(x,y):
                        if tile.feature is not None and not tile.is_blocked():
                            traversible_features.append((tile.feature,
                                                    directions['full names'][(tile.x -x, tile.y - y)]))
                    if len(traversible_features) > 1:
                        self.ui.msgbox("Too many to choose!") #TODO: let them choose
                    elif len(traversible_features) == 1:
                        traversible_features[0][0].interact(player)
                        turns_taken = 1 #TODO: every interaction takes exactly 1 turn, perhaps we want it differentiated
                    else:
                        infotip("Nothing to interact with.")
                elif player_action.startswith('PICK UP'):
                    #TODO: menu to choose a pickup if more than one
                    tile = game.board[player.x, player.y] 
                    if tile.items:
                        for item in [item for item in tile.items]:
                            player.pick_up(item)
                        turns_taken = 1
                    else:
                        infotip("Nothing to pick up.")
                elif player_action.startswith('LEAVE'):
                    if game.current_quest is not None and not game.current_quest.is_finished():
                        infotip("You have to finish your mission or die trying!",'failure')
                    elif [agent for agent in game.agents_in_sight if not agent.is_player() and not agent.flag('incapacitated')] != []:
                        infotip("You can't leave during a fight!",'warning')
                    else:
                        #TODO: hack for projected shield
                        if describe_item(game.player['deployable item'], article = False) == 'stop projecting shield':
                            game.player['deployable item'].use(game.player, 'deployable')
                        game.player.leave()
                        game.state = 'debriefing'                    
                elif player_action.startswith('DROP'):
                    chosen_item = self.inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n', ['droppable'])
                    #TODO: dropping items unfinished
                elif player_action == 'LOOK':
                    self.select_target_tile(exclude_player = False, visible = False, confirm_action = 'LOOK')
                    center_on_player = False
                elif player_action.startswith('SELECT'):
                    tile = self.ui.get_tile_under_mouse()
                    if tile is not None:
                        if tile.occupant is not None and player['ranged item'] is not None and tile.visible:
                            player['ranged item'].use(game.player, 'ranged', tile.occupant)
                            turns_taken = 1
                        else:
                            #TODO: Go (move) to tile
                            if player['ranged item'] is None:
                                message('You point your finger at {1} {0} and say: "Pif paf! You`re dead, {0}!"'.format( \
                                    'darkness' if not tile.visible else tile.occupant.name if tile.occupant is not None else tile.terrain.name, \
                                    grammar.a_or_an(tile.occupant.name) if tile.occupant is not None else 'the'
                                    ), 'joke')
                            else :
                                infotip("Shoot only at enemies, ricochets are dangerous!")
                    else:
                        #TODO: handle HUD elements selection
                        pass
                elif player_action.startswith('INVENTORY'):
                    chosen_item = self.inventory_menu('Press the key next to an item to equip it, or any other to cancel.\n')
                    if chosen_item is not None:
                        player.equip(chosen_item)
                        turns_taken = 1
                elif player_action.startswith('USE'):
                    action_type = player_action[4:]
                    item = player[action_type + ' item']
                    if item is not None:
                        if item[action_type].requires_target:
                            if item.flag('close range'):
                                infotip("You prepare to deploy your {0}...".format(item.name))
                                target = self.select_adjacent_tile(unblocked_only = not item.flag('deployed'))
                            else:
                                infotip("You take aim with your {0}...".format(item.name))
                                max_range = item[action_type]['range'] if 'range' in item[action_type] else None
                                target = self.select_target_tile(occupied = (action_type == 'ranged'), confirm_action = player_action, \
                                                             clear_line = not item.flag('smart aim'), max_range = max_range)
                            if target is None:
                                infotip("Use of " + item.name + " cancelled.")
                            else:
                                turns_taken = 1 if item.use(game.player, action_type, target) else 0
                        else:
                            turns_taken = 1 if item.use(game.player, action_type) else 0
                    else:
                        infotip("Nothing to use in " + player_action[4:] + " slot!")
                else:
                    self.ui.msgbox("Unkown player action: {0}. Please report this bug to {1}!".format(player_action, AUTHOR_EMAIL), 'warning')
            elif game.state == 'dead':
                if player_action in ['QUIT', 'INTERACT']:
                    quit_game = True

        return (turns_taken, quit_game, center_on_player) #TODO: does it make sense

    def inventory_menu(self, header, filters = []):
        #show a menu with each item of the inventory as an option
        #filter_set = set(filters)
        #filtered_inventory = [item for item in game.player.inventory if filter_set.issubset(set(item.flags))]
        filtered_inventory = game.player.inventory 
        if len(filtered_inventory) == 0:
            options = ['Nothing applicable.']
            #TODO: make it a msgboxy inventory
        else:
            options = []
            for item in filtered_inventory:
                option = describe_item(item, article = False) 
                for flag in ['ranged', 'melee', 'consumable', 'deployable', 'activated']:
                    if game.player[flag + ' item'] == item:
                        option += ' (equipped)' 
                options.append(option)
        index = self.ui.menu(header, options)
        #if an item was chosen, return it
        if index is None or len(filtered_inventory) == 0: return None
        return filtered_inventory[index]
    
    def player_act_in_direction(self, direction):
        """ Move or attack or perform other contextual actions.
            TODO: move to Agent class?
        """
        has_results = True
        dx, dy = direction
        #the coordinates the player is moving to/attacking
        x = game.player.x + dx
        y = game.player.y + dy
        if not game.board.contains_position(x,y):
            infotip("It is the edge of the world!")
            return
        #try to find an attackable object there
        target_tile = game.board[x,y]
        if target_tile.is_blocked():
            if target_tile.occupant is not None:
                if target_tile.occupant.is_player():
                    message("You wait.")
                else:
                    if not game.player.melee(target_tile.occupant):
                        has_results = False
            elif target_tile.feature is not None:
                has_results = target_tile.feature.interact(game.player)
            else:
                has_results = False
                if not game.board[game.player.x,game.player.y].terrain.flag('zero g'):
                    infotip("You can't go through the {0}!".format(target_tile.blocking_piece.name))
        elif not game.board[game.player.x,game.player.y].terrain.flag('zero g'):
            game.player.move_to(x, y)
            game.fov_recompute = True
        else:
            has_results = False
        if game.board[game.player.x,game.player.y].terrain.flag('zero g') and not has_results:
            vx, vy = game.player['velocity']
            speed = max(abs(vx), abs(vy))
            game.player['velocity'] = vx + dx, vy + dy
            new_speed = max(abs(vx + dx), abs(vy + dy))
            message("You {0}!".format('adjust direction' if speed == new_speed else 'accelerate' if speed < new_speed else 'decelerate'), 'ion')
             
            has_results = True
        return has_results
    
    def prepare_play(self):
        """ This method:
            1) computes the necessary game data that cannot be handled by 
            game_data module to avoid circular dependencies 
            2) sets other things necessary for the game to be played that
            it would be a waste to do elsewhere.  
        """
        pass
        

        