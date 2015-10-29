#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import random
import time
import thread
import string
import sys

import xbmc
import xbmcaddon
import xbmcgui

from board import Goban, ble

from xbmcgui import (
    ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP,
    ACTION_PAUSE, ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK,
    ACTION_PREVIOUS_MENU, ACTION_NAV_BACK,
    ACTION_SHOW_INFO,
)

DIRECTIONS = [ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP]
SELECT = [
    ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK, ACTION_PAUSE
]
BACK = [ACTION_NAV_BACK]
INFO = [ACTION_SHOW_INFO]
ACTIONS = DIRECTIONS + SELECT + BACK

addon = xbmcaddon.Addon()

ADDON_NAME = addon.getAddonInfo('name')
ADDON_PATH = addon.getAddonInfo('path').decode('utf-8')
MEDIA_PATH = os.path.join(
    xbmc.translatePath(ADDON_PATH),
    'resources',
    'skins',
    'default',
    'media'
)

STRINGS = {
    'you_won_head': 32007,
    'you_won_text': 32008,
    'exit_head': 32009,
    'exit_text': 32012
}


COLUMNS = 19
ROWS = 19


def get_image(filename):
    return os.path.join(MEDIA_PATH, filename)

def _(string_id):
    if string_id in STRINGS:
        return addon.getLocalizedString(STRINGS[string_id])
    else:
        xbmc.log('String is missing: %s' % string_id, level=xbmc.LOGDEBUG)
        return string_id


def log(msg):
    xbmc.log('[ADDON][%s] %s' % (ADDON_NAME, msg.encode('utf-8')),
             level=xbmc.LOGNOTICE)


class Stone(object):

    def __init__(self, x, y, grid, width, height):
        self._x = x
        self._y = y
        self.grid = grid
        self._y_position = self.grid._x_position + width * (grid._rows - x)
        self._x_position = self.grid._y_position + height * y
        self._width = width
        self._height = height
        self.button_control = None
        self.image_control = None

    def build_controls(self):
        self.button_control = xbmcgui.ControlButton(
            x=self._x_position,
            y=self._y_position,
            width=self._width,
            height=self._height,
            label='',
            focusTexture=get_image('selected.png'),
            noFocusTexture=get_image('not_selected.png'),
            #noFocusTexture=get_image('black.png'),
        )
        self.image_control = xbmcgui.ControlImage(
            x=self._x_position,
            y=self._y_position,
            width=self._width,
            height=self._height,
            filename=get_image('empty.png'),
        )

    def place_stone(self, player):
        if player == 'w':
            stone = 'white.png'
        elif player == 'b':
            stone = 'black.png'
        else:
            stone = 'empty.png'
        self.image_control.setImage(get_image(stone))

    def set_navigation(self):
        self.button_control.setNavigation(
            up=self.grid.at(self._x + 1, self._y).button_control,
            right=self.grid.at(self._x, self._y + 1).button_control,
            down=self.grid.at(self._x - 1, self._y).button_control,
            left=self.grid.at(self._x, self._y - 1).button_control,
        )

    @property
    def button_id(self):
        return self.button_control.getId()

    @property
    def pos(self):
        return self._x, self._y

    def __str__(self):
        return '(%d, %d)' % (self._x, self._y)


class Grid(Goban):

    def __init__(self, rows, columns, x_position, y_position, width, height,
                 sgf=None):
        self._rows = rows
        self._columns = columns
        self._x_position = x_position
        self._y_position = y_position
        self._width = width
        self._height = height
        self._grid = []
        self.current = None
        self.stones = {}
        super(Grid, self).__init__(sgf)

    def new_stone(self, x, y, width, height):
        """Add a new stone.

        :param int x: the column in which this stone is
        :param int y: the row that the stone is in
        :param int width: the stone's width
        :param int height: the stone's height
        """
        stone = Stone(x, y, self, width, height)
        stone.build_controls()
        stone.place_stone(self.board.board[x][y])
        return stone

    def setup_stones(self, window):
        """Setup all stones in this grid.

        :param xbmcgui.Window: the window that the controls should be attached to
        """
        width = self._width / self._columns
        height = self._height / self._rows
        self._grid = [
            [self.new_stone(x, y, width, height) for y in xrange(self._columns)]
            for x in xrange(self._rows)
        ]

        stones = [stone for row in self._grid for stone in row]
        # this is done this way as opposed to doing it during stone
        # creation, because it was sloooowwwww
        window.addControls([t.image_control for t in stones])
        window.addControls([t.button_control for t in stones])

        # this couldn't be done earlier, as certain stones could be linked to
        # stones which hadn't yet been created
        for stone in stones:
            self.stones[stone.button_id] = stone
            stone.set_navigation()

    def remove_stones(self, window):
        """Remove all stones from this grid.

        :param xbmcgui.Window: the window that the controls were attached to
        """
        stones = self.stones.values()
        window.removeControls([t.button_control for t in stones])
        window.removeControls([t.image_control for t in stones])
        self.stones = {}
        self._grid = []

    def refresh_board(self):
        for x in xrange(self._columns):
            for y in xrange(self._rows):
                self._grid[x][y].place_stone(self.board.board[x][y])

    @property
    def all_correct(self):
        return False

    def at(self, row, column):
        self._pos = (row, column)
        return self._grid[row % self._rows][column % self._columns]

    def handle(self, action, focused):
        """Handle the guven action.

        :param xbmcgui,Action action: the action
        :param int focused: the id of the focused button
        :returns: whether the action was handled
        """
        action_id = action.getId()
        try:
            self.current = self.stones[focused]
            if action_id in SELECT:
                self.move(*self.current.pos)
                self.random_move()
            elif action_id in BACK:
                self.back()
                self.back()
            else:
                return False
            self.refresh_board()
            return True
        except KeyError as e:
            pass


class Game(xbmcgui.WindowXML):
    CONTROL_ID_GRID = 3001
    CONTROL_ID_RESTART = 3002
    CONTROL_ID_MOVES_COUNT = 3003
    CONTROL_ID_TARGET_COUNT = 3004
    CONTROL_ID_TIME = 3005
    CONTROL_ID_EXIT = 3006
    CONTROL_ID_GAME_ID = 3007

    def onInit(self):
        # init vars
        self._stone_button_ids = {}
        self._game_in_progress = False
        self._game_id = ''
        # get controls
        self.grid_control = self.getControl(self.CONTROL_ID_GRID)
        self.target_control = self.getControl(self.CONTROL_ID_TARGET_COUNT)
        self.moves_control = self.getControl(self.CONTROL_ID_MOVES_COUNT)
        self.time_control = self.getControl(self.CONTROL_ID_TIME)
        self.game_id_control = self.getControl(self.CONTROL_ID_GAME_ID)
        self.new_game_control = self.getControl(self.CONTROL_ID_RESTART)
        # init the grid
        self.grid = self.get_grid()
        self.grid.setup_stones(self)
        self.add_stone_controls()
        # start the timer thread
        thread.start_new_thread(self.timer_thread, ())
        # start the game
        self.start_game()

    def onAction(self, action):
        """Handle the given action.

        If the action is not one that is to be handled, it will be passed on.
        """
        action_id = action.getId()
        log('pressed %d' % action_id)
        if action_id == xbmcgui.ACTION_QUEUE_ITEM:
            return self.exit()
        if self.grid.handle(action, self.getFocusId()):
            return
        if action_id in INFO:
                pass
        super(Game, self).onAction(action)

    def onFocus(self, control_id):
        pass

    def onClick(self, control_id):
        if control_id == self.CONTROL_ID_RESTART:
            self.start_game()
        elif control_id == self.CONTROL_ID_EXIT:
            self.exit()

    def get_grid(self):
        # get xml defined position and dimension for the grid
        x, y = self.grid_control.getPosition()
        width = self.grid_control.getWidth()
        height = self.grid_control.getHeight()
        return Grid(ROWS, COLUMNS, x, y, width, height, ble)

    def start_game(self, game_id=None):
        self._game_in_progress = True
        self._start_time = time.time()
        self._moves = 0
        self._target_moves = 'bla'
        self.moves_control.setLabel(str(self._moves))
        self.target_control.setLabel(str(self._target_moves))
        self.game_id_control.setLabel(str(self._game_id))

    def add_stone_controls(self):
        # set onleft on the new game button to the upper right stone
        upper_right_stone = self.grid.at(ROWS - 1, COLUMNS - 1)
        self.new_game_control.controlLeft(upper_right_stone.button_control)
        # set onRight on the upper right stone to the new game button
        upper_right_stone.button_control.controlRight(self.new_game_control)

    def game_over(self):
        self._game_in_progress = False
        dialog = xbmcgui.Dialog()
        dialog.ok(_('you_won_head'), _('you_won_text'))

    def exit(self):
        dialog = xbmcgui.Dialog()
        confirmed = dialog.yesno(_('exit_head'), _('exit_text'))
        if confirmed:
            self.grid.remove_controls(window)
            self.close()

    def movement_done(self):
        self._moves += 1
        self.moves_control.setLabel(str(self._moves))


if __name__ == '__main__':
    game = Game(
        'script-%s-main.xml' % ADDON_NAME,
        ADDON_PATH,
        'default',
        '720p'
    )
    game.doModal()
    del game

sys.modules.clear()
