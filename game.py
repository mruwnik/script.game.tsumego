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

import traceback

import xbmc
import xbmcaddon
import xbmcgui

from xbmc import LOGDEBUG, LOGNOTICE, LOGERROR, LOGSEVERE, LOGFATAL
from xbmcgui import (
    ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP,
    ACTION_PAUSE, ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK,
    ACTION_PREVIOUS_MENU, ACTION_NAV_BACK,
    ACTION_SHOW_INFO,
    REMOTE_1, REMOTE_2, REMOTE_3, REMOTE_4,
    REMOTE_5, REMOTE_6, REMOTE_7, REMOTE_8, REMOTE_9,
)

from resources.lib.board import Goban
from resources.lib.problems import Problems, MockProblems

DIRECTIONS = [ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP]
SELECT = [
    ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK, ACTION_PAUSE
]
BACK = [ACTION_NAV_BACK]
INFO = [ACTION_SHOW_INFO]
HOSHI_POINTS = [
    REMOTE_1, REMOTE_2, REMOTE_3, REMOTE_4,
    REMOTE_5, REMOTE_6, REMOTE_7, REMOTE_8, REMOTE_9,
]
ACTIONS = DIRECTIONS + SELECT + BACK + HOSHI_POINTS

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
DATA_PATH = os.path.join(
    xbmc.translatePath(ADDON_PATH), "resources", "data", "problems")

STRINGS = {
    'show_solution': 32002,
    'hide_solution': 32003,
    'off_path': 32015,
    'solved': 32016,
    'exit_head': 32009,
    'exit_text': 32012,
    'current_rank': 32013,
    'rating': 32014,
}


COLUMNS = 19
ROWS = 19

class ControlIds(object):
    GRID = 3001
    NEXT = 3002
    RESTART = 3003
    SOLUTION = 3004

    ERROR = 3015
    SUCCESS = 3016
    COMMENTS = 3017
    rank = 3018
    rating = 3019


class KeyCodes(object):
    a = 61505
    d = 61508
    g = 61511
    l = 61516
    n = 61518
    o = 61519
    t = 61524
    u = 61515
    v = 61526
    w = 61527
    y = 61529
    z = 61530


def get_image(filename):
    return os.path.join(MEDIA_PATH, filename)

def _(string_id):
    if string_id in STRINGS:
        return addon.getLocalizedString(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id, LOGDEBUG)
        return string_id


def log(msg, level=LOGNOTICE):
    xbmc.log('[ADDON][%s] %s' % (ADDON_NAME, msg.encode('utf-8')), level=level)


class Tile(object):

    def __init__(self, x, y, grid, width, height):
        self.x = x
        self.y = y
        self.grid = grid
        self.y_position = self.grid.x + width * (grid.rows - x)
        self.x_position = self.grid.y + height * y
        self.width = width
        self.height = height
        self.add_controls()

    def add_controls(self):
        pass

    @property
    def controls(self):
        return []

    def next(self, direction):
        """Get the next spot in the given direction, wrapping arount the edges.

        :param int direction: a keyboard arrow code
        :rtype: Tile
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


class Grid(object):

    def __init__(self, rows, columns, x, y, width, height, *args, **kwargs):
        self.rows = rows
        self.columns = columns
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tile_width = self.width / self.columns
        self.tile_height = self.height / self.rows
        self.grid = []
        self.current = None
        self.right = None
        self.window = None
        self.add_controls()
        super(Grid, self).__init__(*args, **kwargs)

    def add_controls(self):
        self.control = xbmcgui.ControlButton(
            x=self.x,
            y=self.y,
            width=self.tile_width,
            height=self.tile_height,
            label=''
        )
        self.position_marker = xbmcgui.ControlImage(
            x=self.x,
            y=self.y,
            width=self.tile_width,
            height=self.tile_height,
            filename=get_image('selected.png'),
        )

    def setup_labels(self):
        """Set up all labels."""
        pass

    @property
    def labels(self):
        return []

    def new_tile(self, x, y):
        """Add a new tile.

        :param int x: the column in which this tile is
        :param int y: the row that the tile is in
        """
        return Tile(x, y, self, self.tile_width, self.tile_height)

    def add_label(self, x, y, label):
        return xbmcgui.ControlLabel(
            x=self.y + self.tile_height * y,
            y=self.x + self.tile_width * (self.rows - x),
            width=self.tile_width,
            height=self.tile_height,
            label='[B]%s[/B]' % label,
            font='font30',
#            textColor='0xFFFF3300',
            alignment=2
        )

    def setup_tiles(self, window, right_control):
        """Setup all tiles in this grid.

        :param xbmcgui.Window: the window that the controls should be attached to
        :param xbmcgui.Control: the control that is to the right of the grid
        """
        self.grid = [
            [self.new_tile(x, y) for y in xrange(self.columns)]
            for x in xrange(self.rows)
        ]

        # postition the marker on the upper right corner
        self.current = self.grid[self.columns - 1][0]
        self.position_marker.setPosition(
            *self.grid[self.columns - 1][self.rows - 1].display_pos
        )

        # this is done this way as opposed to doing it during tile
        # creation, because it was sloooowwwww
        tile_controls = [c for row in self.grid for tile in row for c in tile.controls]
        controls = [self.position_marker, self.control]

        window.addControls(tile_controls + controls)

        # connect the control to the right with this grid
        right_control.controlLeft(self.control)
        self.right = right_control

        self.window = window
        self.setup_labels()
        self.update_labels()

    def update_labels(self):
        """Add any labels, removing the old ones if found."""
        try:
            old_labels = self.label_controls
        except AttributeError:
            pass
        else:
            self.window.removeControls(old_labels)

        self.label_controls = [self.add_label(x, y, label) for (x, y), label in self.labels]
        self.window.addControls(self.label_controls)

    def remove_tiles(self, window):
        """Remove all tiles from this grid.

        :param xbmcgui.Window: the window that the controls were attached to
        """
        tile_controls = [c for row in self.grid for tile in row for c in tile.controls]
        controls = [self.position_marker, self.control]
        window.removeControls(tile_controls + controls + self.label_controls)
        self.grid = []

    @property
    def size(self):
        return self.rows, self.columns

    def at(self, row, column):
        return self.grid[row % self.rows][column % self.columns]

    def handle(self, action, focused):
        """Handle the given action.

        :param xbmcgui,Action action: the action
        :param int focused: the id of the focused button
        :returns: whether the action was handled, or None if nothing was done
        """
        # if a different control is focused, move the current tile
        # to the left most one, so that it will get rolled over when
        # control returns to the grid
        if focused != self.control.getId():
            self.current = self.grid[self.current.x][0]
            return False
        self.control.controlRight(self.control)

        try:
            action_id = action.getId()
            if action_id in DIRECTIONS:
                self.current = self.current.next(action_id)
                self.position_marker.setPosition(*self.current.display_pos)
                if self.current.y == self.size[1] - 1:
                    self.control.controlRight(self.right)
                return True
            else:
                return self.handle_key(action_id)
        except KeyError as e:
            log(str(e))

    def handle_key(self, key):
        """Handle the given key code.

        :returns: whether the key was handled
        """
        pass


class Stone(Tile):

    def __init__(self, *args, **kwargs):
        super(Stone, self).__init__(*args, **kwargs)
        self._mark = ''
        self.player = None
        self.stone = None

    def add_controls(self):
        self.image = xbmcgui.ControlImage(
            x=self.x_position,
            y=self.y_position,
            width=self.width,
            height=self.height,
            filename=get_image('empty.png'),
        )

    @property
    def controls(self):
        return [self.image]

    def mark(self, mark_type=''):
        """Mark this stone with the given marker."""
        self._mark = mark_type

    def place_stone(self, player):
        """Place a stone for the given player on this spot.

        To remove a stone, pass None

        :param str or None player: the code of the player to be placed
        """
        if player == 'w':
            self.player = 'white'
        elif player == 'b':
            self.player = 'black'
        else:
            self.player = None

        if player == 'good' or player == 'bad':
            stone = '%s_spot.png' % player
        elif not self.player:
            stone = 'empty.png'
        elif self._mark:
            stone = '%s_%s.png' % (self.player, self._mark)
        else:
            stone = '%s.png' % self.player

        if stone != self.stone:
            self.stone = stone
            self.image.setImage(get_image(stone))


class GobanGrid(Grid, Goban):
    hoshi = {
        REMOTE_1: (3, 3),
        REMOTE_2: (3, 9),
        REMOTE_3: (3, 15),
        REMOTE_4: (9, 3),
        REMOTE_5: (9, 9),
        REMOTE_6: (9, 15),
        REMOTE_7: (15, 3),
        REMOTE_8: (15, 9),
        REMOTE_9: (15, 15),
    }

    def __init__(self, *args, **kwargs):
        self.comments_box = None
        self.hints = False
        self.problems = Problems(DATA_PATH)
        super(GobanGrid, self).__init__(*args, **kwargs)

    def setup_labels(self):
        """Set up all status messages and the comments box."""
        window = self.window
        self.current_rank = window.getControl(ControlIds.rank)
        self.rating_box = window.getControl(ControlIds.rating)
        self.comments_box = window.getControl(ControlIds.COMMENTS)
        self.error_control = window.getControl(ControlIds.ERROR)
        self.success_control = window.getControl(ControlIds.SUCCESS)
        self.success_control.setLabel(_('solved'))
        self.error_control.setLabel(_('off_path'))

        self.update_comment()
        self.update_messages()

    @property
    def labels(self):
        """Get the labels of the current node from the board."""
        return Goban.labels.fget(self)

    def new_tile(self, x, y):
        """Add a new stone.

        :param int x: the column in which this stone is
        :param int y: the row that the stone is in
        """
        stone = Stone(x, y, self, self.tile_width, self.tile_height)
        if self.board:
            stone.place_stone(self.board.board[x][y])
        return stone

    def refresh_board(self):
        """Refresh the contents of the grid."""
        if not self.grid:
            log('No grid found during board refresh', LOGDEBUG)
            return

        self.update_comment()

        # make sure all marks are set
        for x, y in self.marks:
            self.grid[x][y].mark('mark')
        for x, y in self.triangles:
            self.grid[x][y].mark('triangle')
        for x, y in self.marks:
            self.grid[x][y].mark()
        for x, y in self.marks:
            self.grid[x][y].mark()

        # refresh all points
        for x in xrange(self.columns):
            for y in xrange(self.rows):
                pos = (x, y)
                if pos in self.marks:
                    self.grid[x][y].mark('mark')
                elif pos in self.triangles:
                    self.grid[x][y].mark('triangle')
                elif pos in self.squares:
                    self.grid[x][y].mark('square')
                elif pos in self.circles:
                    self.grid[x][y].mark('circle')
                elif pos in self.marks:
                    self.grid[x][y].mark('mark')
                else:
                    self.grid[x][y].mark()
                self.grid[x][y].place_stone(self.board.board[x][y])
        self.mark_hints()

    def load(self, sgf=None):
        """Load the given SGF, or reload the current one if none provided.

        :param (str or None) sgf: the SGF to be loaded
        """
        log(str(sgf))
        super(Grid, self).load(sgf)
        self.refresh_board()

    def next(self):
        """Load the next problem."""
        # loop over problems until a good one is found
        for problem in self.problems:
            self.problem = problem
            try:
                self.load(self.problem['sgf'])
            except ValueError:
                continue
            except IndexError:
                log('board was too small')
                traceback.print_exc()
            else:
                self.hints = False
                self.position_marker.setImage(get_image("shadow_%s.png" % self.next_player_name))
                self.update_messages()
                self.update_labels()
                self.current_rank.setText(_('current_rank') % self.problems.rank)
                self.rating_box.setText(
                    _('rating') % tuple([self.problem['rating']] + list(self.problem['rank'])))
                return

    def toggle_hints(self, state=None):
        """Toggle the display of hints on the board.

        :param boolean state: this can be used to force the state
        :returns: whether or not hints are shown
        """
        if 'solved' not in self.problem:
            self.problems.failure(self.problem['rank'], 0.4)
            self.problem['solved'] = False
        self.hints = state if state is not None else not self.hints
        self.mark_hints()
        return self.hints

    def update_comment(self, comment=None):
        """Set the comment to the given comment, or the current SGF comment.

        If no comment is provided, the comment of the current SGF node will
        be displayed.

        :param str or None comment: the comment to be displayed
        """
        if not self.comments_box:
            log('No comments box found during comment refresh', LOGDEBUG)
            return

        if comment is None:
            comment = self.current_comment.replace('FORCE', '').replace('RIGHT', '')
        self.comments_box.setText(comment)

    def update_messages(self):
        """Update the status messages' visibility."""
        self.error_control.setVisible(bool(self.board and not self.on_path))
        self.success_control.setVisible(bool(self.board and self.correct))

    def mark_hints(self):
        """Mark all hints on the board."""
        if not self.hints:
            return

        def mark_node(node, mark=None):
            """Mark a single hint on the board.

            :param str mark: what the marker should be
            """
            _, (x, y) = node.get_move()
            self.grid[x][y].place_stone(mark)

        # get rid of any previous markers - the grandparent must be used,
        # because the parent is automatically placed and has no hints
        if self.node.parent and self.node.parent.parent:
            map(mark_node, filter(lambda v: v != self.node, self.node.parent.parent))

        for child in self.node:
            mark_node(child, 'good' if self.correct_path(child) else 'bad')

    def handle_key(self, key):
        """Handle the given key.

        :param int key: the key code
        :returns: whether the action was handled
        """
        if not self.board:
            return
        if key in SELECT:
            self.move(*self.current.pos)
            self.random_move()
            self.position_marker.setImage(get_image("shadow_%s.png" % self.next_player_name))
            self.update_messages()
            self.update_labels()
            if 'solved' not in self.problem and self.correct:
                self.problems.success(self.problem['rank'])
                self.problem['solved'] = True
        elif key in BACK:
            if 'solved' not in self.problem:
                self.problems.failure(self.problem['rank'])
                self.problem['solved'] = False
            self.back()
            self.back()
            self.update_messages()
            self.update_labels()
        elif key in HOSHI_POINTS:
            x, y = self.hoshi[key]
            self.current = self.grid[x][y]
            self.position_marker.setPosition(*self.current.display_pos)
        else:
            return False
        self.refresh_board()
        return True


class Game(xbmcgui.WindowXML):
    def onInit(self):
        log('initialising')
        # get controls
        self.grid_control = self.getControl(ControlIds.GRID)
        self.next_control = self.getControl(ControlIds.NEXT)
        self.solution_control = self.getControl(ControlIds.SOLUTION)

        # init the grid
        self.grid = self.get_grid()

    def onAction(self, action):
        """Handle the given action.

        If the action is not one that is to be handled, it will be passed on.
        """
        try:
            action_id = action.getId()
            log(str(action_id))
            if action_id == xbmcgui.ACTION_QUEUE_ITEM:
                return self.exit()
            elif self.grid.handle(action, self.getFocusId()):
                return
            elif action_id in INFO:
                pass
            elif action.getButtonCode() == KeyCodes.n:
                self.grid.next()
        except Exception as e:
            traceback.print_exc()
        super(Game, self).onAction(action)

    def onFocus(self, control_id):
        pass

    def onClick(self, control_id):
        if control_id == ControlIds.RESTART:
            self.restart_game()
        elif control_id == ControlIds.SOLUTION:
            self.solution_control.setLabel(
                _('hide_solution' if self.grid.toggle_hints() else 'show_solution')
            )
        elif control_id == ControlIds.NEXT:
            self.grid.next()

    def get_grid(self, sgf=None):
        try:
            grid = self.grid
        except AttributeError:
            grid = None

        if not grid:
            # get xml defined position and dimension for the grid
            x, y = self.grid_control.getPosition()
            grid = GobanGrid(
                ROWS, COLUMNS, x=x, y=y,
                width=self.grid_control.getWidth(),
                height=self.grid_control.getHeight(),
            )
            grid.setup_tiles(self, self.next_control)
            grid.next()
        else:
            grid.remove_tiles(self)
            grid.setup_tiles(self, self.next_control)

        return grid

    def restart_game(self):
        self.grid.load(self.grid.sgf)
        self.grid.update_messages()

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
