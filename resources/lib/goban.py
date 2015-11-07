# -*- coding: utf-8 -*-

import traceback

import xbmcaddon
import xbmcgui

from xbmcgui import (
    ACTION_PAUSE, ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK,
    ACTION_PREVIOUS_MENU, ACTION_NAV_BACK,
    REMOTE_1, REMOTE_2, REMOTE_3, REMOTE_4,
    REMOTE_5, REMOTE_6, REMOTE_7, REMOTE_8, REMOTE_9,
)

from resources.lib.log_utils import log, _
from resources.lib.grid import Grid, Tile, get_image
from resources.lib.board import Goban
from resources.lib.problems import Problems, MockProblems

SELECT = [
    ACTION_SELECT_ITEM, ACTION_PARENT_DIR, ACTION_MOUSE_LEFT_CLICK, ACTION_PAUSE
]
BACK = [ACTION_NAV_BACK]

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

addon = xbmcaddon.Addon()


class ControlIds(object):
    goban = 4001
    error = 3015
    success = 3016
    comments = 3017
    rank = 3018
    rating = 3019


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

    def hide(self):
        """Hide all controls in this tile."""
        self.image.setVisible(False)
        self.set_marker(None)

    def mark(self, mark_type=''):
        """Mark this stone with the given marker."""
        self._mark = mark_type

    def set_marker(self, player):
        """Set the appropriate marker on this spot.

        To remove a stone, pass None

        :param str or None player: the code of the player to be placed
        """
        if player == 'w':
            self.player = 'white'
        elif player == 'b':
            self.player = 'black'
        elif not player:
            self.player = None

        if player == 'good' or player == 'bad':
            stone = '%s_spot.png' % player
        elif not player:
            stone = 'empty.png'
        elif player in ['w', 'b']:
            if self._mark:
                stone = '%s_%s.png' % (self.player, self._mark)
            else:
                stone = '%s.png' % self.player
        else:
            stone = '%s.png' % player

        if stone != self.stone:
            self.stone = stone
            self.image.setImage(get_image(stone))


class GobanGrid(Grid, Goban):


    def __init__(self, *args, **kwargs):
        self.comments_box = None
        self.hints = False
        self.load_problems(
            problems_dir=kwargs.pop('problems_dir', addon.getSetting('problems_dir')),
            rank=kwargs.pop('rank', addon.getSetting('rank')),
        )
        super(GobanGrid, self).__init__(*args, **kwargs)

    def load_problems(self, problems_dir, rank=None):
        """Load all problems found in the given directory.

        :param str problems_dir: where to look for tsumego
        :param str rank: the current rank of the user.
        """
        if not rank and self.problems:
            rank = self.problems.pretty_rank
        self.problems = Problems(problems_dir, rank)

    def setup_labels(self):
        """Set up all status messages and the comments box."""
        window = self.window
        self.current_rank = window.getControl(ControlIds.rank)
        self.rating_box = window.getControl(ControlIds.rating)
        self.comments_box = window.getControl(ControlIds.comments)
        self.error_control = window.getControl(ControlIds.error)
        self.success_control = window.getControl(ControlIds.success)
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
            stone.set_marker(self.board.board[x][y])
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
        for x in xrange(self.game.get_size()):
            for y in xrange(self.game.get_size()):
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
                self.grid[x][y].set_marker(self.board.board[x][y])
        self.mark_hints()

    def set_size(self, size):
        """Set the board size and refresh what is displayed."""
        if size <= 9:
            actual_size = 9
            if self.rows > 9:
                self.window.getControl(ControlIds.goban).setImage('goban9.png')
        elif 9 < size <= 13:
            actual_size = 13
            if 9 <= self.rows or self.rows > 13:
                self.window.getControl(ControlIds.goban).setImage('goban13.png')
        elif size > 13:
            actual_size = 19
            if 13 <= self.rows:
                self.window.getControl(ControlIds.goban).setImage('goban19.png')

        super(GobanGrid, self).set_size(actual_size)
        # if the board is irregular (i.e. not 9x9, 13x13 or 19x19), make sure
        # that the pointer is correctly set, and that any tiles outside the
        # boundaries are correctly hidden
        if size < actual_size:
            self.rows = size
            self.columns = size
            current_x = self.current.x if self.current.x < size else size - 1
            current_y = self.current.y if self.current.y < size else size - 1
            self.select(self.grid[current_x][current_y])
            # hide all tiles that shouldn't be shown
            for p1 in xrange(0, actual_size):
                for p2 in xrange(size, actual_size):
                    self.grid[p1][p2].set_marker('wall')
                    self.grid[p2][p1].set_marker('wall')

    def load(self, sgf=None):
        """Load the given SGF, or reload the current one if none provided.

        :param (str or None) sgf: the SGF to be loaded
        """
        log(str(sgf))
        super(Grid, self).load(sgf)
        if self.game:
            self.set_size(self.game.get_size())
            self.refresh_board()

    def next(self):
        """Load the next problem.

        If no problem can be loaded, an error message is displayed.
        """
        # loop over problems until a good one is found
        for problem in self.problems:
            self.problem = problem
            try:
                self.load(self.problem['sgf'])
            except (ValueError, IndexError):
                traceback.print_exc()
            else:
                log('board size: %d' % self.game.get_size())
                self.hints = False
                self.position_marker.setImage(get_image("shadow_%s.png" % self.next_player_name))
                self.update_messages()
                self.update_labels()
                self.current_rank.setText(_('current_rank') % self.problems.rank)
                if self.problem.get('rank'):
                    rating = self.problem.get('rating') or 0
                    rank_value, rank = self.problem.get('rank')
                    self.rating_box.setText(_('rating') % (rating, rank_value, rank))
                else:
                    self.rating_box.setText('')
                return
        else:
            level = self.problems.level
            ranks = map(
                lambda rank: '%d %s' % rank,
                map(self.problems.get_rank, [level + 3, level - 3])
            )
            self.comments_box.setText(_('no_problems_found') % tuple(ranks))

    def problem_solved(self, solved, weight=0.25):
        """Mark whether this problem was solved or not.

        :param boolean solved: whether the problem was solved
        :param float weight: the wieght of the solution.
        """
        if 'solved' in self.problem:
            return

        if solved:
            self.problems.success(self.problem['rank'], weight)
        else:
            self.problems.failure(self.problem['rank'], weight)
        self.problem['solved'] = solved
        addon.setSetting('level', self.problems.pretty_rank)

    def toggle_hints(self, state=None):
        """Toggle the display of hints on the board.

        :param boolean state: this can be used to force the state
        :returns: whether or not hints are shown
        """
        self.problem_solved(False, 0.4)
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
            self.grid[x][y].set_marker(mark)

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
            if self.correct:
                self.problem_solved(True)
        elif key in BACK:
            self.problem_solved(False)
            self.back()
            self.back()
            self.update_messages()
            self.update_labels()
        elif key in hoshi:
            x, y = hoshi[key]
            self.current = self.grid[x][y]
            self.position_marker.setPosition(*self.current.display_pos)
        else:
            return False
        self.refresh_board()
        return True

