# -*- coding: utf-8 -*-
import os

import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.log_utils import log

from xbmcgui import (
    ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP,
)

DIRECTIONS = [ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP]

addon = xbmcaddon.Addon()

ADDON_PATH = addon.getAddonInfo('path').decode('utf-8')
MEDIA_PATH = os.path.join(
    xbmc.translatePath(ADDON_PATH),
    'resources',
    'skins',
    'default',
    'media'
)


def get_image(filename):
    return os.path.join(MEDIA_PATH, filename)


class Tile(object):

    def __init__(self, x, y, grid, width, height):
        self.grid = grid
        self.set_position(x, y, width, height)
        self.add_controls()

    def set_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.x_position = self.grid.y + height * y
        self.y_position = self.grid.x + width * (self.grid.rows - 1 - x)
        self.width = width
        self.height = height

    def hide(self):
        """Hide all controls in this tile."""
        pass

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

    def reposition(self, x, y, width, height):
        self.set_position(x, y, width, height)
        for control in self.controls:
            control.setHeight(self.height)
            control.setWidth(self.width)
            control.setPosition(self.x_position, self.y_position)
            control.setVisible(True)

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
            y=self.x + self.tile_width * (self.rows - 1 - x),
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

    def set_size(self, rows, columns=None):
        """Set the grid's size.

        :param int rows: the new amount of rows
        :param int columns: the new amount of columns. If not provided, 'rows' is used
        """
        if not columns:
            columns = rows
        if rows == self.rows and columns == self.columns:
            return

        self.rows = rows
        self.columns = columns

        # start off by hiding all tiles. This gets rid of any artifacts on the
        # screen
        for row in self.grid:
            for tile in row:
                tile.hide()

        # reposition/resize all tile still in the new boundaries
        self.tile_width = self.width / rows
        self.tile_height = self.height / columns
        for x in xrange(rows):
            for y in xrange(columns):
                self.grid[x][y].reposition(x, y, self.tile_width, self.tile_height)

        # if the previous selection was out of bounds, select the closest
        # tile that is still visible
        current_x = self.current.x if self.current.x < rows else rows - 1
        current_y = self.current.y if self.current.y < columns else columns - 1
        self.select(self.grid[current_x][current_y])

        for control in self.control, self.position_marker:
            control.setWidth(self.tile_width)
            control.setHeight(self.tile_height)

    def at(self, row, column):
        return self.grid[row % self.rows][column % self.columns]

    def select(self, tile):
        """Select the given tile as the current one.

        :param Tile tile: the current tile.
        """
        self.current = tile
        self.position_marker.setPosition(*self.current.display_pos)
        if self.current.y == self.size[1] - 1:
              self.control.controlRight(self.right)

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
                self.select(self.current.next(action_id))
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

