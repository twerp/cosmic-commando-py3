'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from os import sep
import ConfigParser

class GameSettings(object):
    FOV_ALGO = 6  #TODO: make sure its FOV_PERMISSIVE_3 by using explicit const from libtcod
    FOV_LIGHT_WALLS = True

GAME_TITLE = 'Cosmic Commando'
GAME_VERSION = '0.3' 

AUTHOR_EMAIL = "zasvid+roguelike@gmail.com"

ASSET_DIR = 'assets'
parser = ConfigParser.ConfigParser()
parser.read('coscom.cfg')
FONT = ASSET_DIR + sep + parser.get('main','font')
SCREEN_WIDTH = parser.getint('screen','width')
SCREEN_HEIGHT = parser.getint('screen','height')


SCREEN_TITLE = "{0} v. {1}".format(GAME_TITLE, GAME_VERSION)
IMAGE_COSCOM = ASSET_DIR+sep+'koskom.png'
IMAGE_RAVEN = ASSET_DIR+sep+'koskom.png'

DEBUG_NO_FOG = True

INFO_WIDTH = 50

MSG_BOX_WIDTH = 50


LIMIT_FPS = 20

GAME_ACTION_TIMEOUT = 1.5

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 30
HUD_WIDTH = BAR_WIDTH + 4
HUD_HEIGHT = SCREEN_HEIGHT
HUD_Y = 0
HUD_X = SCREEN_WIDTH - HUD_WIDTH

MSG_X = HUD_X
MSG_WIDTH = HUD_WIDTH - 2

#TODO: allow the board to be displayed not in the upper left corner
#CAMERA_X = 0
#CAMERA_Y = 0
CAMERA_WIDTH = SCREEN_WIDTH - HUD_WIDTH
CAMERA_HEIGHT = SCREEN_HEIGHT



