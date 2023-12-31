# coding=UTF-8
#!/usr/bin/python
''' Cosmic Commando - a roguelike game.    
    Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
from guts.debug import debug
from guts.game_system import GameSystem

if __name__ == '__main__':
    if 'debug' in sys.argv:
        debug.activate()
    GameSystem().main_menu()

