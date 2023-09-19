# coding=UTF-8
'''
This code is part of Cosmic Commando; Copyright (C) 2012-2013 Piotr 'ZasVid' Sikora; see CosmicCommando.py for full notice.
'''

from guts.config import *
from guts.visuals import shape, color
from guts.game_data import game
from guts.game_agents import item_action_types
import guts.libtcodpy as libtcod
from guts.debug import debug
from guts.libtcod_tables import _special_keys
from guts.player_input import input_manager
import guts.grammar as grammar
from guts.game_description import describe_item
from os import putenv

class UI(object):
    MENU_NUMERIC_INDEX = 'numeric'
    MENU_CUSTOM_INDEX = 'custom'
    MENU_ALPHABET_INDEX = 'alphabet'
    MENU_NUMCOMBO_INDEX = 'numeric/custom'
    MAX_OPTIONS = {'numeric' : 10, 'numeric/custom':10, 'alphabet' : 26, 'custom' : 255, 'hard lock' : 0}
    MENU_HARD_LOCK = 'hard lock'
    
    def __init__(self):
        font_flags = None
        if FONT.find('_tc') >= 0:
            font_flags = libtcod.FONT_LAYOUT_TCOD
        elif FONT.find('_incol') >= 0:
            font_flags = libtcod.FONT_LAYOUT_ASCII_INCOL
        else:
            font_flags = libtcod.FONT_LAYOUT_ASCII_INROW
        if FONT.find('_gs'):
            font_flags |= libtcod.FONT_TYPE_GRAYSCALE
        putenv("SDL_VIDEO_CENTERED", "1")
        libtcod.console_set_custom_font(FONT, font_flags)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, False)
        self.board_display = libtcod.console_new(CAMERA_WIDTH, CAMERA_HEIGHT)
        self.hud = libtcod.console_new(HUD_WIDTH, HUD_HEIGHT)
        libtcod.sys_set_fps(LIMIT_FPS)
        #self.camera_x = CAMERA_X
        #self.camera_y = CAMERA_Y
        self.camera_x = 0
        self.camera_y = 0
        self.mouse_pos = None
        self._targeting_path = []

    def clear(self):
        libtcod.console_set_default_background(0, color('black'))
        libtcod.console_clear(None)

    def _set_camera_to(self, x, y):
        #make sure the camera doesn't see outside the map
        if x < 0: x = 0
        if y < 0: y = 0
        if x > game.board.width - CAMERA_WIDTH : x = max(0, game.board.width - CAMERA_WIDTH)
        if y > game.board.height - CAMERA_HEIGHT: y = max(0, game.board.height - CAMERA_HEIGHT) 
        (self.camera_x, self.camera_y) = (x, y)

    def center_camera(self, x, y):
        centered_x = x - CAMERA_WIDTH / 2  #coordinates so that the target is at the center of the screen
        centered_y = y - CAMERA_HEIGHT / 2
        self._set_camera_to(centered_x, centered_y)
    
    def move_camera(self, dx, dy):
        new_x = self.camera_x + dx
        new_y = self.camera_y + dy
        self._set_camera_to(new_x, new_y)
    
    def cell_in_camera_view(self, x, y):
        ''' Checks if display cell of x, y coordinates is in board camera view '''
        ''' TODO: make modifications for a camera in other parts of the display than upper left corner '''
        if x < 0 or x >= min(CAMERA_WIDTH, game.board.width):
            return False
        if y < 0 or y >= min(CAMERA_HEIGHT, game.board.height):
            return False
        return True

    def get_tile_under_mouse(self):
        mouse = libtcod.mouse_get_status()
        (x, y) = (mouse.cx, mouse.cy)
        if self.cell_in_camera_view(x,y):
            return game.board[self.camera_x + x, self.camera_y + y]  #from screen to map coordinates
        return None
    
    def render_gfx(self):
        for board_x, board_y, color_name in game.graphical_effects:
            x, y = (board_x - self.camera_x, board_y - self.camera_y)
            if self.cell_in_camera_view(x, y):
                libtcod.console_set_char_background(self.board_display, x, y, color(color_name), flag = libtcod.BKGND_SET)
        libtcod.console_blit(self.board_display, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)
        game.graphical_effects = []
    
    def render_targeting(self, line):
        self._clear_targeting()
        target_clear = True
        for p in line.points:
            x, y = (p.x - self.camera_x, p.y - self.camera_y)
            if self.cell_in_camera_view(x, y):
                highlight_color_name = 'target clear' if target_clear else 'target blocked'
                libtcod.console_set_char_background(self.board_display, x, y, color(highlight_color_name), flag = libtcod.BKGND_SET) 
                self._targeting_path.append((x,y))
                if p == line.blocking_point: 
                    target_clear = False
        #intensify the final cell colour:
        x, y = self._targeting_path[-1]
        libtcod.console_set_char_background(self.board_display, x,y, 'white', flag=libtcod.BKGND_COLOR_DODGE)
        libtcod.console_blit(self.board_display, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)
    
    def _clear_targeting(self):
        for x,y in self._targeting_path:
            libtcod.console_set_char_background(self.board_display, x, y, color('black'), flag= libtcod.BKGND_SET)
        self._targeting_path = []
        
    def wipe_targeting(self):
        self._clear_targeting()
        libtcod.console_blit(self.board_display, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)
    
    def render_all(self, center_on_player):
        if game.fov_check():
            libtcod.console_clear(self.board_display)
        if center_on_player:
            self.center_camera(game.player.x, game.player.y)
        self.render_board()
        self.render_hud()
        
    def _render_bar(self, x, y, total_width, name, value, maximum, bar_color, bkgnd_color, text_color = 'white', centered = True, display_numbers = True):
        if centered:
            libtcod.console_set_alignment(self.hud, libtcod.CENTER)
        #render a bar (HP, experience, etc). first calculate the width of the bar
        bar_width = int(float(min(value, maximum)) / maximum * total_width)
        #render the background first
        libtcod.console_set_default_background(self.hud, color(bkgnd_color))
        libtcod.console_rect(self.hud, x, y, total_width, 1, False, libtcod.BKGND_SET)
        #now render the bar on top
        libtcod.console_set_default_background(self.hud, color(bar_color))
        if bar_width > 0:
            libtcod.console_rect(self.hud, x, y, bar_width, 1, False, libtcod.BKGND_SET)
        #finally, some centered text with the values
        libtcod.console_set_default_foreground(self.hud, color(text_color))
        text_x_adjust = (total_width / 2) if centered else 0
        libtcod.console_print(self.hud, x + text_x_adjust, y,
                                    "{0}{1}".format(name, ": {0}/{1}".format(value, maximum) if display_numbers else ''))
                                     
    
    def clear_hud(self):
        #prepare to render the HUD
        libtcod.console_set_default_background(self.hud, libtcod.black)
        libtcod.console_clear(self.hud)
    
    def render_mouseover_info(self, only_this = True):
        #TODO: work it out
        #display names of objects under the mouse TODO: only once per render all? Not in a turn game, no.
        #libtcod.console_set_default_foreground(self.hud, color('light gray'))
        #libtcod.console_print(self.hud, 1, 0, str(self.get_tile_under_mouse()))
        #if only_this:
        #   libtcod.console_blit(self.hud, 0, 0, SCREEN_WIDTH, HUD_HEIGHT, 0, 0, HUD_Y)
        pass

    def print_rectangle(self, console, x, y, width, height, text, text_color):
        rect_height = libtcod.console_get_height_rect(console, x, y, width, height, text)
        libtcod.console_set_default_foreground(console, color(text_color))
        libtcod.console_print_rect(console, x, y, width, height, text)            
        return rect_height     
    
    def render_hud(self):
        self.clear_hud()    
        #show the player's stats
        y = 0
        libtcod.console_set_default_foreground(self.hud, color('ui text'))
        libtcod.console_set_alignment(self.hud, libtcod.LEFT)
        #libtcod.console_print(self.hud, 1, y, 'At: ')
        #y += 1
        objectives_descs = []
        if game.current_quest is not None:
            y += self.print_rectangle(self.hud, 1, y, MSG_WIDTH, HUD_HEIGHT - y, game.current_quest.description, 'ui text')
            for objective in game.current_quest.objectives.values():
                if objective.is_available():
                    if objective.is_fulfilled():
                        objective_color = 'failure' if objective.is_negative() else 'completed quest'
                    else:
                        objective_color = 'warning' if objective.is_negative() else 'tracked quest'
                    objectives_descs.append((objective.description, objective_color))
        else:
            #for quest tracking functionality
            objectives_descs.append(("No quest tracked at this time.", 'completed quest'))
        for objective_desc, desc_color in objectives_descs:
            y += self.print_rectangle(self.hud, 1, y, MSG_WIDTH, HUD_HEIGHT - y, objective_desc, desc_color)
        y+=1
        for trait, bg_color in [('health', 'blood red'), ('shields', 'waning shields')]:
            self._render_bar(2, y, BAR_WIDTH, grammar.capitalise(trait), game.player[trait], game.player['max '+ trait], trait, bg_color)
            y += 1
        libtcod.console_set_alignment(self.hud, libtcod.LEFT)
        if debug.active and game.player['velocity'] != (0,0):
            libtcod.console_set_default_foreground(self.hud, color('ion'))
            libtcod.console_print(self.hud, 1, y, 'Velocity: {0}'.format(game.player['velocity']))
            y += 1
        y += 1
        hud_items = []
        for item_type in item_action_types:
            item = game.player[item_type + ' item']
            hud_heat = (item['heat'],item['heat capacity']) if item is not None and item.flag('heats') else None 
            key = input_manager.key_of('USE ' + item_type)
            hud_key = '[{0}] '.format(key) if key is not None else 'melee: '
            hud_text = '-- nothing equipped --' if item is None else describe_item(item, article = False)
            hud_color = 'white' if item is None else item.color
            hud_items.append((hud_heat, hud_key, hud_text, hud_color))
        key_width = max([len(hud_item[1]) for hud_item in hud_items])
        for hud_heat, hud_key, hud_text, hud_color in hud_items:
            libtcod.console_set_default_foreground(self.hud, color(hud_color))
            libtcod.console_print(self.hud, 1, y, hud_key.ljust(key_width))
            x = 1 + key_width
            if hud_heat is None:
                libtcod.console_print(self.hud, x, y, hud_text)
            else:
                heat, heat_cap = hud_heat
                self._render_bar(x, y, BAR_WIDTH - x, hud_text, heat, heat_cap, 'heat', 'heat capacity', hud_color, False, False)
            y += 1 
        libtcod.console_set_default_foreground(self.hud, color('ui'))
                
        libtcod.console_hline(self.hud, 1, y, HUD_WIDTH)
        y += 1
        """print the game's volatile info, that should not clutter the message log needlessly
            e.g. interface tips, inconsequential warnings, repeatedly requestable map info 
        """
        for (infotip, msg_color) in game.infotips:  
            y += self.print_rectangle(self.hud, 1, y, MSG_WIDTH, HUD_HEIGHT - y, infotip, msg_color)

        libtcod.console_set_default_foreground(self.hud, color('ui'))
        libtcod.console_hline(self.hud, 1, y, HUD_WIDTH)
        y += 1
        #print the game messages, one line at a time
        MSG_HEIGHT = HUD_HEIGHT - y
        for (line, msg_color) in game.msgs[(-1) * MSG_HEIGHT:]:
            libtcod.console_set_default_foreground(self.hud, color(msg_color))    
            libtcod.console_print(self.hud, 1, y, line) 
            y += 1
        #if the buffer is overly full, empty it somewhat to not put giant logs of duplicated messages into savefiles
        if len(game.msgs) > HUD_HEIGHT:
            del game.msgs[0:len(game.msgs) - HUD_HEIGHT]
        #blit the contents of HUD to the root console
        libtcod.console_blit(self.hud, x = 0, y = 0, w = HUD_WIDTH, h = HUD_HEIGHT, dst = 0, xdst = HUD_X, ydst = HUD_Y)

    def render_board(self):
        for y in range(min(CAMERA_HEIGHT, game.board.height)):
            for x in range(min(CAMERA_WIDTH, game.board.width)):
                (board_x, board_y) = (self.camera_x + x, self.camera_y + y)
                visible = libtcod.map_is_in_fov(game.fov_map, board_x, board_y)
                tile = game.board[board_x, board_y]
                tile.visible = visible
                libtcod.console_put_char_ex(self.board_display, x, y, shape(tile.shape), color(tile.color), color(tile.highlight))
                if (board_x, board_y) in game.overlays:
                    libtcod.console_set_char_background(self.board_display, x, y, color(game.overlays[(board_x, board_y)]), flag = libtcod.BKGND_SET)
        libtcod.console_blit(self.board_display, 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)

    def listbox(self, header, list_items, width = MSG_BOX_WIDTH, default_text_color = 'white', margins = True, scroll_to_bottom = False):
        self.menu(header, list_items, width, indexing = None, default_text_color = default_text_color, margins = margins, scroll_to_bottom = scroll_to_bottom)

    def msgbox(self, text, default_text_color = 'white', width = MSG_BOX_WIDTH, margins = False, hard_lock = False):
        #use menu() as a sort of "message box"
        if hard_lock:
            self.menu(text, [], width, indexing = UI.MENU_HARD_LOCK, default_text_color = default_text_color, margins = margins)
        else:
            self.menu(text, [], width, default_text_color = default_text_color, margins = margins)   

    def menu(self, header, items, width = MSG_BOX_WIDTH, indexing = MENU_ALPHABET_INDEX, \
             case_sensitive = False, default_text_color = 'ui text', margins = False, scroll_to_bottom = False):
        """ TODO: enhance the menu to be capable of containing more
                 options than the height of the screen would allow - 
                 renumeration of options to those fitting the screen a la ADOM would work.
        """
        ui_color = color('ui')
        margin_width = 2 if margins else 0
        header_width = width - 2 * margin_width
        content_width = width - 2 * margin_width
        if indexing is not None and len(items) > UI.MAX_OPTIONS[indexing]:
            raise ValueError('Cannot have a menu with ' + indexing + \
                             " indexing with more than " + UI.MAX_OPTIONS[indexing] + ' options.')
        #calculate total height for the header (after auto-wrap) and one line per option
        if isinstance(header, tuple):
            header_text, header_color = header
        else:
            header_text = header
            header_color = default_text_color
            
        header_height = libtcod.console_get_height_rect(0, 0, 0, header_width, SCREEN_HEIGHT, header_text) \
                        if header_text != '' else 0
        #margins_height = 0 if not margins else 1 if header_height > 0 else 2 #top margin only needed separately if no header
        top_margin_height = 2 if margins else 0
        bottom_margin_height = 1 if margins else 0
        margins_height = top_margin_height + bottom_margin_height 
        #prepare all the options
        if indexing == UI.MENU_ALPHABET_INDEX:
            start_index = ord('a')
        else:
            start_index = ord('0')
        letter_index = start_index
        option_indices = []
        item_displays = []
        total_item_height = 0
        for item_tuple in items:
            if indexing in [UI.MENU_CUSTOM_INDEX, UI.MENU_NUMCOMBO_INDEX]:
                option_index = item_tuple[1]
                item_text = '(' + option_index  + ') ' + item_tuple[0]
                item_color = item_tuple[2] if len(item_tuple) == 3 and item_tuple[2] else default_text_color
                option_index_ord = ord(option_index) if case_sensitive else ord(option_index.lower())
                if option_index_ord in option_indices:
                    debug.log("Menu: " + header + " contains two options with the same index: " + option_index)
                option_indices.append(option_index_ord)
            if indexing != UI.MENU_CUSTOM_INDEX:
                item_text = '' if indexing is None else '(' + chr(letter_index) + ') '
                item_text += item_tuple[0] if isinstance(item_tuple, tuple) else item_tuple
                if indexing != UI.MENU_NUMCOMBO_INDEX:
                    item_color = item_tuple[1] if len(item_tuple) == 2 and item_tuple[1] else default_text_color
                letter_index += 1
            # item displays contain text, color, height
            item_displays.append((item_text, color(item_color), libtcod.console_get_height_rect(0, 0, 0, content_width, SCREEN_HEIGHT, item_text)))
            total_item_height += item_displays[-1][2]

        #create the display
        height = min(sum([item_display[2] for item_display in item_displays]) + header_height + margins_height, SCREEN_HEIGHT)
        #create an off-screen console that represents the menu's window
        window = libtcod.console_new(width, height)
        max_item_height = height - bottom_margin_height
        
        def last_page_offset(item_displays, max_height):
            #TODO: improve to work on a line by line basis - probably needs tweaking to the whole menu code :D
            #TODO: compute it once per menu, perhaps?
            i = -1
            last_page_height = 0
            while last_page_height < max_height and i > -len(item_displays):
                last_page_height += item_displays[i][2]
                i -= 1
            return len(item_displays) + i + 3 if last_page_height >= max_height else 0
        
        item_offset = last_page_offset(item_displays, max_item_height) if scroll_to_bottom else 0 #TODO: scroll to bottom
        while True:
            libtcod.console_clear(window)
            #print the header, with auto-wrap
            libtcod.console_set_default_foreground(window, color(header_color))
            libtcod.console_set_alignment(window, libtcod.LEFT)
            header_y = 1 if margins else 0
            libtcod.console_print_rect(window, margin_width, header_y, header_width, header_height, header_text)
            #make margins:
            libtcod.console_set_default_foreground(window, ui_color)
            if margins:
                libtcod.console_print(window, 0, header_y - 1, '*' + '-' * (width - 2) + '*')
                libtcod.console_print_rect(window, 0, header_y, margin_width, header_height, '* ' * (header_height+1))
                libtcod.console_print_rect(window, width - margin_width, header_y, margin_width, header_height, ' *' * (header_height+1))
                libtcod.console_print(window, 0 , header_height + header_y, '*' + '-' * (width - 2) + '*')
            y = header_height + top_margin_height
            last_message_index = 0
            for item_text, item_color, item_height in item_displays[item_offset:]:
                libtcod.console_set_default_foreground(window, item_color)
                libtcod.console_print_rect(window, margin_width, y, content_width, item_height, item_text)
                #make margins:
                libtcod.console_set_default_foreground(window, ui_color)
                if margins:
                    libtcod.console_print_rect(window, 0, y, margin_width, item_height, '| ' * item_height)
                    libtcod.console_print_rect(window, width - margin_width + 1, y, 1, item_height, '|' * item_height)
                y += item_height
                if y > max_item_height:
                    break
                last_message_index += 1
            if margins:
                if total_item_height > max_item_height:
                    scroll_help_message = ' Press Arrow/Page Up/Down to scroll '
                else:
                    scroll_help_message = ''
                margin_bar = '-' * (width/2 - 1 - len(scroll_help_message)/2)
                libtcod.console_print(window, 0 , min(y, height - 1), '*' + margin_bar + scroll_help_message + margin_bar + '*')
            #blit the contents of "window" to the root console
            blit_x = SCREEN_WIDTH/2 - width/2
            blit_y = max(SCREEN_HEIGHT/2 - height/2 - 1, 0)
            bg_transparency = 1.0 if total_item_height > max_item_height else 0.7
            libtcod.console_blit(window, 0, 0, width, height, 0, blit_x, blit_y, 1.0, bg_transparency)
            #present the root console to the player and wait for a key-press
            libtcod.console_flush()
            key, mouse = libtcod.Key(), libtcod.Mouse()
            #while not libtcod.console_is_window_closed():
            while True:
                libtcod.sys_wait_for_event(libtcod.EVENT_KEY_RELEASE, key, mouse, True)
                if key.vk not in [libtcod.KEY_NONE, libtcod.KEY_CONTROL, libtcod.KEY_ALT, libtcod.KEY_SHIFT]:
                    if indexing == UI.MENU_HARD_LOCK:
                        if key.vk in [libtcod.KEY_ENTER, libtcod.KEY_ESCAPE, libtcod.KEY_SPACE]:
                            break
                    else:
                        break
            #convert the ASCII code to an index; if it corresponds to an option, return it
            if indexing in [UI.MENU_CUSTOM_INDEX, UI.MENU_NUMCOMBO_INDEX]:
                for i in range(len(option_indices)):
                    key_ord = key.c if case_sensitive else ord(chr(key.c).lower())
                    if key_ord == option_indices[i]:
                        return i
            if indexing != UI.MENU_CUSTOM_INDEX:
                key_ord = key.c if case_sensitive else ord(chr(key.c).lower())
                index = key_ord - start_index
                if index >= 0 and index < len(items): return index
            if total_item_height > max_item_height:
                if key.vk == libtcod.KEY_UP:
                    item_offset = max(0, item_offset - 1)
                elif key.vk == libtcod.KEY_DOWN:
                    item_offset = min(last_page_offset(item_displays, max_item_height), item_offset + 1)
                elif key.vk == libtcod.KEY_PAGEUP:
                    item_offset = max(0, item_offset - 10)
                elif key.vk == libtcod.KEY_PAGEDOWN:
                    item_offset = min(last_page_offset(item_displays, max_item_height), item_offset + 10)
                elif key.vk == libtcod.KEY_HOME:
                    item_offset = 0
                elif key.vk == libtcod.KEY_END:
                    item_offset = last_page_offset(item_displays, max_item_height)
                else:
                    return None
            else:
                return None

    def pointer_selection(self):
        """ Returns an element of the interface pointed at by the mouse cursor.
            This might be a tile, a menu line or something else.
            TODO: implement
        """
        pass

    def get_input(self):
        """ Alternatively, CTRL and ALT could be left out of this, disallowed as modifiers
            and used for commands (crouch!). Holding the keys for an auxiliary command would
            also be possible and perhaps even useful in a real-time roguelike.
        """
        """ Mouse status from libtcod contains fields:
            x,y,dx,dy - position and change of position in pixels
            cx, cy, dcx, dcy - position and change of position in cells - note: dcx, dcy might not update properly according to a forum thread
            lbutton, rbutton, mbutton - True if the button is still pressed
            lbutton_pressed, rbutton_pressed, mbutton_pressed - True if there was a click (press and release)
            wheel_up, wheel_down - undocumented, looks to be boolean, so I guess this would be "has the wheel been scrolled up/down since last check?"
        """

        key, mouse, inputs = libtcod.Key(), libtcod.Mouse(), []
        if game.is_time_limited():
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_RELEASE | libtcod.EVENT_MOUSE, key, mouse)
        else:
            libtcod.sys_wait_for_event(libtcod.EVENT_KEY_RELEASE | libtcod.EVENT_MOUSE, key, mouse, True)
        self.mouse_pos = (mouse.cx, mouse.cy)
        if key.lalt or key.ralt:
            inputs.append('alt')
        if key.rctrl or key.lctrl:
            inputs.append('ctrl')
        if key.vk == libtcod.KEY_CHAR:
            inputs.append(chr(key.c))
        elif key.vk not in [libtcod.KEY_NONE, libtcod.KEY_CONTROL, libtcod.KEY_ALT, libtcod.KEY_SHIFT]:
            if key.shift:
                inputs.append('shift')
            inputs.append(_special_keys[key.vk])
        else:
            if mouse.lbutton_pressed:
                inputs.append('left click')
            elif mouse.rbutton_pressed:
                inputs.append('right click')
            elif mouse.mbutton_pressed:
                inputs.append('middle click')
        #print(str(inputs))
        return inputs
     
