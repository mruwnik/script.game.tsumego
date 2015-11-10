#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import thread
import sys

import traceback

import xbmcaddon
import xbmcgui

from xbmcgui import (
    ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP,
    ACTION_SHOW_INFO,
)

from resources.lib.goban import GobanGrid
from resources.lib.log_utils import log, _


DIRECTIONS = [
    ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP
]
INFO = [ACTION_SHOW_INFO]

addon = xbmcaddon.Addon()

COLUMNS = 19
ROWS = 19


class ControlIds(object):
    grid = 3001
    next_problem = 3002
    restart = 3003
    solution = 3004

    clock = 3020


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


class Game(xbmcgui.WindowXML):
    def onInit(self):
        log('initialising')
        # get controls
        self.grid_control = self.getControl(ControlIds.grid)
        self.next_control = self.getControl(ControlIds.next_problem)
        self.solution_control = self.getControl(ControlIds.solution)
        self.clock = self.getControl(ControlIds.clock)
        self.clock_thread = thread.start_new_thread(self.clock_ticker, tuple())

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
                self.settings()
            elif action.getButtonCode() == KeyCodes.n:
                self.solution_control.setLabel(_('show_solution'))
                self.grid.next()
        except Exception:
            traceback.print_exc()
        super(Game, self).onAction(action)

    def onFocus(self, control_id):
        pass

    def onClick(self, control_id):
        if control_id == ControlIds.restart:
            self.restart_game()
        elif control_id == ControlIds.solution:
            self.solution_control.setLabel(
                _('hide_solution' if self.grid.toggle_hints() else 'show_solution')  # noqa
            )
        elif control_id == ControlIds.next_problem:
            self.solution_control.setLabel(_('show_solution'))
            self.grid.next()

    def get_grid(self):
        """Get or create the board's grid and set it up with a problem."""
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
        self.solution_control.setLabel(_('show_solution'))
        self.grid.load(self.grid.sgf)
        self.grid.problem_solved(False)
        self.grid.update_messages()

    def settings(self):
        """Display the setting dialog."""
        dialog = xbmcgui.Dialog()
        problems_dir = dialog.browse(
            0, _('get_problems_dir'), 'files', '', False, False, None
        )
        if problems_dir:
            addon.setSetting('problems_dir', problems_dir)
            self.grid.load_problems(problems_dir)
            self.grid.next()

    def exit(self):
        dialog = xbmcgui.Dialog()
        confirmed = dialog.yesno(_('exit_head'), _('exit_text'))
        if confirmed:
            self.grid.remove_controls(self)
            self.close()

    def clock_ticker(self):
        """Update the clock if the minute changes."""
        current_minute = time.time() // 60
        while True:
            if current_minute != (time.time() // 60):
                current_minute = time.time() // 60
                self.clock.setText(time.strftime('%H:%M', time.localtime()))
            time.sleep(1)


if __name__ == '__main__':
    game = Game(
        'script-%s-main.xml' % addon.getAddonInfo('name'),
        addon.getAddonInfo('path').decode('utf-8'),
        'default',
        '720p'
    )
    game.doModal()
    del game

sys.modules.clear()
