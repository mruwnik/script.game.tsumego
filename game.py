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

from board import Goban, ble, bla

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
        self.x = x
        self.y = y
        self.grid = grid
        self.y_position = self.grid.x + width * (grid.rows - x)
        self.x_position = self.grid.y + height * y
        self.width = width
        self.height = height
        self.image = xbmcgui.ControlImage(
            x=self.x_position,
            y=self.y_position,
            width=self.width,
            height=self.height,
            filename=get_image('empty.png'),
        )

    def place_stone(self, player):
        """Place a stone for the given player on this spot.

        To remove a stone, pass None

        :param str or None player: the code of the player to be placed
        """
        if player == 'w':
            stone = 'white.png'
        elif player == 'b':
            stone = 'black.png'
        else:
            stone = 'empty.png'
        self.image.setImage(get_image(stone))

    def next(self, direction):
        """Get the next spot in the given direction, wrapping arount the edges.

        :param int direction: a keyboard arrow code
        :rtype: Stone
        :return: the next spot in the given direction
        """
        if direction == ACTION_MOVE_DOWN:
            return self.grid.at(self.x - 1, self.y)
        elif direction == ACTION_MOVE_LEFT:
            return self.grid.at(self.x, self.y - 1)
        elif direction == ACTION_MOVE_RIGHT:
            return self.grid.at(self.x, self.y + 1)
        elif direction == ACTION_MOVE_UP:
            return self.grid.at(self.x + 1, self.y)

    @property
    def pos(self):
        """Get the position on the board."""
        return self.x, self.y

    @property
    def display_pos(self):
        """Get the position on the screen."""
        return self.x_position, self.y_position

    def __str__(self):
        return '(%d, %d)' % (self.x, self.y)


class Grid(Goban):

    def __init__(self, rows, columns, x, y, width, height, sgf):
        super(Grid, self).__init__(sgf)
        self.rows = rows
        self.columns = columns
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.stone_width = self.width / self.columns
        self.stone_height = self.height / self.rows
        self.grid = []
        self.current = None
        self.right = None
        self.comments_box = None
        self.add_controls()

    def add_controls(self):
        self.control = xbmcgui.ControlButton(
            x=self.x,
            y=self.y,
            width=self.stone_width,
            height=self.stone_height,
            label=''
        )
        self.position_marker = xbmcgui.ControlImage(
            x=self.x,
            y=self.y,
            width=self.stone_width,
            height=self.stone_height,
            filename=get_image('shadow_%s.png' % self.next_player_name),
        )

    def new_stone(self, x, y):
        """Add a new stone.

        :param int x: the column in which this stone is
        :param int y: the row that the stone is in
        """
        stone = Stone(x, y, self, self.stone_width, self.stone_height)
        stone.place_stone(self.board.board[x][y])
        return stone

    def add_label(self, x, y, label):
        return xbmcgui.ControlLabel(
            x=self.y + self.stone_height * y,
            y=self.x + self.stone_width * (self.rows - x),
            width=self.stone_width,
            height=self.stone_height,
            label='[B]%s[/B]' % label,
            font='font30',
#            textColor='0xFFFF3300',
            alignment=2
        )

    def setup_stones(self, window, right_control, comments):
        """Setup all stones in this grid.

        :param xbmcgui.Window: the window that the controls should be attached to
        :param xbmcgui.Control: the control that is to the right of the grid
        """
        # add any labels
        self.label_controls = [self.add_label(x, y, label) for (x, y), label in self.labels]

        self.grid = [
            [self.new_stone(x, y) for y in xrange(self.columns)]
            for x in xrange(self.rows)
        ]
        self.current = self.grid[self.columns - 1][self.rows - 1]

        # this is done this way as opposed to doing it during stone
        # creation, because it was sloooowwwww
        stones = [stone.image for row in self.grid for stone in row]
        controls = [self.position_marker, self.control]

        window.addControls(stones + controls + self.label_controls)

        # connect the control to the right with this grid
        right_control.controlLeft(self.control)
        self.right = right_control

        self.comments_box = comments
        self.update_comment()

    def remove_stones(self, window):
        """Remove all stones from this grid.

        :param xbmcgui.Window: the window that the controls were attached to
        """
        stones = [stone.image for row in self.grid for stone in row]
        controls = [self.position_marker, self.control]
        window.removeControls(stones + controls + self.label_controls)
        self.grid = []

    def refresh_board(self, previous_state=None):
        """Refresh the contents of the grid.

        If the previous state is provided, only the places that changed
        will be refreshed, otherwise the whole grid will be redrawn.

        :param list previous_state: a list of lists with the previous state
        """
        for x in xrange(self.columns):
            for y in xrange(self.rows):
                if not previous_state or self.board.board[x][y] != previous_state[x][y]:
                    self.grid[x][y].place_stone(self.board.board[x][y])

    @property
    def size(self):
        return self.rows, self.columns

    @property
    def all_correct(self):
        return False

    def at(self, row, column):
        return self.grid[row % self.rows][column % self.columns]

    def update_comment(self, comment=None):
        if comment is None:
            comment = self.current_comment.replace('FORCE', '').replace('RIGHT', '')
        self.comments_box.setText(comment)

    def handle(self, action, focused):
        """Handle the guven action.

        :param xbmcgui,Action action: the action
        :param int focused: the id of the focused button
        :returns: whether the action was handled
        """
        # if a different control is focused, move the current spot
        # to the left most one, so that it will get rolled over when
        # control returns to the grid
        if focused != self.control.getId():
            self.current = self.grid[self.current.x][0]
            return False
        self.control.controlRight(self.control)

        action_id = action.getId()
        try:
            prev_state = self.board.copy().board
            if action_id in SELECT:
                self.move(*self.current.pos)
                self.random_move()
                self.position_marker.setImage(get_image("shadow_%s.png" % self.next_player_name))
                self.update_comment()
            elif action_id in BACK:
                self.back()
                self.back()
            elif action_id in DIRECTIONS:
                self.current = self.current.next(action_id)
                self.position_marker.setPosition(*self.current.display_pos)
                if self.current.y == self.size[1] - 1:
                    self.control.controlRight(self.right)
            else:
                return False
            self.refresh_board(prev_state)
            return True
        except KeyError as e:
            log(str(e))
            pass

class Game(xbmcgui.WindowXML):
    CONTROL_ID_GRID = 3001
    CONTROL_ID_RESTART = 3002
    CONTROL_ID_ERROR = 3003
    CONTROL_ID_SUCCESS = 3004
    CONTROL_ID_TIME = 3005
    CONTROL_ID_EXIT = 3006
    CONTROL_ID_GAME_ID = 3007
    CONTROL_ID_COMMENTS = 3008

    def onInit(self):
        log('initialising')
        # init vars
        self._game_id = ''
        # get controls
        self.grid_control = self.getControl(self.CONTROL_ID_GRID)
        self.error_control = self.getControl(self.CONTROL_ID_ERROR)
        self.success_control = self.getControl(self.CONTROL_ID_SUCCESS)
        self.time_control = self.getControl(self.CONTROL_ID_TIME)
        self.game_id_control = self.getControl(self.CONTROL_ID_GAME_ID)

        self.success_control.setLabel('Solved')
        self.error_control.setLabel('Off path')
        self.success_control.setVisible(False)
        self.error_control.setVisible(False)

        self.reset_control = self.getControl(self.CONTROL_ID_RESTART)
        self.comments_box = self.getControl(self.CONTROL_ID_COMMENTS)
        # init the grid
        self.grid = self.get_grid()
        # start the timer thread
        #thread.start_new_thread(self.timer_thread, ())
        # start the game

    def onAction(self, action):
        """Handle the given action.

        If the action is not one that is to be handled, it will be passed on.
        """
        try:
            action_id = action.getId()
            if action_id == xbmcgui.ACTION_QUEUE_ITEM:
                return self.exit()
            elif self.grid.handle(action, self.getFocusId()):
                if action_id in SELECT:
                    self.error_control.setVisible(not self.grid.good_path)
                    self.success_control.setVisible(self.grid.correct)
                return
            elif action_id in INFO:
                pass
        except Exception as e:
            log(str(e))
        super(Game, self).onAction(action)

    def onFocus(self, control_id):
        pass

    def onClick(self, control_id):
        if control_id == self.CONTROL_ID_RESTART:
            self.restart_game()
        elif control_id == self.CONTROL_ID_EXIT:
            self.exit()

    def get_grid(self):
        try:
            grid = self.grid
        except AttributeError:
            grid = None

        if not grid:
            # get xml defined position and dimension for the grid
            x, y = self.grid_control.getPosition()
            width = self.grid_control.getWidth()
            height = self.grid_control.getHeight()
            grid = Grid(ROWS, COLUMNS, x, y, width, height, bla)
        else:
            grid.remove_stones(self)
        grid.setup_stones(self, self.reset_control, self.comments_box)
        return grid

    def restart_game(self):
        self.grid.remove_stones(self)
        self.grid = None
        self.get_grid()

    def game_over(self):
        dialog = xbmcgui.Dialog()
        dialog.ok(_('you_won_head'), _('you_won_text'))

    def exit(self):
        dialog = xbmcgui.Dialog()
        confirmed = dialog.yesno(_('exit_head'), _('exit_text'))
        if confirmed:
            self.grid.remove_controls(window)
            self.close()


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
