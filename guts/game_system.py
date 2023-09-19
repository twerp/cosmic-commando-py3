# -*- coding: utf-8 -*-
'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from . import libtcodpy as libtcod
import os
from .config import *
from .ui import UI
from sys import exc_info
from .gameplay import GamePlay
from .achievements import Achievements
from .visuals import color

class GameSystem(object):
    '''
    This class handles setting the game up.
    '''

    def __init__(self):
        self.ui = UI()
        self.achievements = Achievements()

    def main_menu(self):
        img_left = libtcod.image_load(IMAGE_COSCOM)
        img_right = libtcod.image_load(IMAGE_RAVEN)
        while not libtcod.console_is_window_closed():
            #show the background image, at twice the regular console resolution
            self.ui.clear()
            #TODO: adjust for screen parameters
            libtcod.image_blit_2x(img_left, 0, 0, 2)
            libtcod.image_blit_2x(img_right, 0, 50, 2)
            
            #show the game's title, and some credits!
            libtcod.console_set_default_foreground(0, color('gold'))
            libtcod.console_set_alignment(0, libtcod.CENTER)
            libtcod.console_print(0, SCREEN_WIDTH/2, 3,  GAME_TITLE.upper())
            libtcod.console_print(0, SCREEN_WIDTH/2, 4,  'v. {0}'.format(GAME_VERSION))
            libtcod.console_print(0, SCREEN_WIDTH/2, SCREEN_HEIGHT - 4, 'by ZasVid')
            libtcod.console_print(0, SCREEN_WIDTH/2, SCREEN_HEIGHT - 3, AUTHOR_EMAIL)
            #show options and wait for the player's choice
            #choice = self.ui.menu('', [('Instructions','i'), ('Play a new game', 'p'), ('Continue last game','c'), ('Quit','q')], 24, indexing = UI.MENU_CUSTOM_INDEX)
            choice = self.ui.menu('', [('[C]redits', 'c'),
                                       ('Continue [l]ast game', 'l'),
                                       ('Play a [n]ew game', 'n'),
                                       ('Play a new game with [t]ime limited turns', 't'),
                                       ('[Q]uit','q'),
                                       #('Play a [t]est game', 't'),
                                       ],
                                  24, indexing = UI.MENU_NUMCOMBO_INDEX, default_text_color = 'ui text')
            if choice == 0: #credits? manual? something like that
                self.ui.msgbox("Credits : \n" \
                               "ZasVid - game design, programming\n" \
                               "Irinka - writing \n" \
                               "\nThis roguelike is powered by libtcod library ( http://doryen.eptalys.net/ ), "
                               "\nThis work contains bits of open-source code from: \n" \
                               "* Joao F. Henriques (a.k.a. Jotaf)'s python + libtcod tutorial (BSD license)\n" \
                               "\nThanks to: \n" \
                               "* contributors to http://roguebasin.roguelikedevelopment.org\n" \
                               "* rogalikator.pl for years of fanning the flame of roguelike passion\n" \
                               "* and last but not least (quite the opposite, in fact), my greatest supporter, lovely Irineczka\n"
                               ,
                               width = SCREEN_WIDTH - 4,
                               default_text_color = 'player' 
                               )#TODO: João
            elif choice == 3:  #new game, time limited turns
                self.gameplay = GamePlay(self.ui, self.achievements)
                self.gameplay.new(time_limit = True)
                self.gameplay.play()
            elif choice == 2:  #new game
                self.gameplay = GamePlay(self.ui, self.achievements)
                self.gameplay.new()
                self.gameplay.play()
            elif choice == 1:  #load last game
                savefile = "savegame"
                if os.path.exists(savefile):
                    try:
                        self.gameplay = GamePlay(self.ui, self.achievements)
                        self.gameplay.load(savefile)
                    except:
                        self.ui.msgbox('\n Failed to load a save: \n'+str(exc_info()), 24)
                        continue
                    self.gameplay.play()
                else:
                    self.ui.msgbox('\n No saved game to load.\n',)
            elif choice == 4:  #quit
                break
            elif choice == 5:
                self.gameplay = GamePlay(self.ui, self.achievements)
                self.gameplay.test()
                self.gameplay.play()
