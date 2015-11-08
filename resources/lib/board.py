"""A representation of a goban, with various helper methods."""
# -*- coding: utf-8 -*-

from random import choice

from gomill import sgf, sgf_moves


class Goban(object):

    """A representation of a goban."""

    def __init__(self, *args, **kwargs):
        """Initialise the goban from the given SGF string."""
        self.sgf = None
        self.game = None
        self.board = None
        self.node = None
        self.load(kwargs.pop('sgf_string', ''))

    def load(self, sgf_string):
        """load the given SGF string."""
        if not sgf_string:
            return
        self.sgf = sgf_string
        self.game = sgf.Sgf_game.from_string(sgf_string)
        self.board, _ = sgf_moves.get_setup_and_moves(self.game)
        self.node = self.root
        self.initial_nodes = self.get_descendants(self.node)

    @classmethod
    def correct_path(cls, node):
        """Check whether the given node lies on the (or a) correct path."""
        return (node.has_property('C') and 'RIGHT' in node.get('C')) \
            or any(cls.correct_path(n) for n in node)

    @classmethod
    def get_descendants(cls, node):
        """Get all descendantsof the given node.

        The resulting list is a nested, recursive list of all descendants.
        """
        children = [
            grandkid for kid in node for grandkid in cls.get_descendants(kid)
        ]
        return [node] + children

    def _move(self, node, player, pos):
        """Place a stone on the board.

        If the resulting place is a known variant, return that node. Otherwise
        create a new node and return it.

        :param node: the current node
        :param 'b' or 'w': the player that is to play
        :param tuple: the position where the stone is to be placed
        """
        current_state = self.board.copy().board
        self.board.play(pos[0], pos[1], player)
        for n in node:
            player, move = n.get_move()
            if move == pos:
                break
        else:
            n = node.new_child()
            n.set_move(player, pos)

        # work out how to recreate the previous state
        size = self.game.get_size()
        n.diff = [
            (x, y, current_state[x][y])
            for x in xrange(size) for y in xrange(size)
            if current_state[x][y] != self.board.board[x][y]
        ]
        return n

    def move(self, x, y):
        """Place the next player's stone on the given spot.

        The position is counted from the bottom left corner (as a cartesian
        coordinate).
        """
        self.node = self._move(self.node, self.next_player, (x, y))

    def back(self):
        """Go back one move, updated the board."""
        if self.node.parent:
            for x, y, player in self.node.diff:
                self.board.board[x][y] = player
            self.node = self.node.parent

    def random_move(self):
        """Chose a random move from the current node, and play it."""
        if self.on_path and len(self.node) > 0:
            self.move(*choice(self.node).get_move()[1])

    def __str__(self):
        """Return this board's current layout as a string."""
        return '\n'.join(
            "|".join(i if i else ' ' for i in x)
            for x in reversed(self.board.board)
        )

    @property
    def root(self):
        """Get the game's root node."""
        return self.game.get_root() if self.game else None

    @property
    def current_player(self):
        """Return the current player as 'w', 'b' or None."""
        return self.node.get_move()[0]

    @property
    def next_player(self):
        """Get the next player.

        If the current player is known, then return the other one. If it's
        not known, but the next step is known, return that step's player.
        Otherwise just assume that it's a new game and return black.
        """
        if not self.board:
            return None
        elif self.current_player:
            return 'b' if self.current_player == 'w' else 'w'
        elif len(self.node) > 0:
            return self.node[0].get_move()[0]
        else:
            return 'b'

    @property
    def next_player_name(self):
        """Return the pretty name of the next player."""
        return 'white' if self.next_player == 'w' else 'black'

    @property
    def current_comment(self):
        """Return the comments of the current node."""
        if self.node is None:
            return ''
        try:
            return self.node.get('C')
        except KeyError:
            try:
                return self.node.get('c')
            except KeyError:
                pass
        return ''

    @property
    def on_path(self):
        """Whether the current path is one of the original ones."""
        return self.node in self.initial_nodes

    @property
    def good_path(self):
        """Whether the current path is one of the correct ones."""
        return self.correct_path(self.node)

    @property
    def correct(self):
        """Whether the current node is a correct end one."""
        return 'RIGHT' in self.current_comment

    def _get_property(self, prop):
        """Get the given property from the current node.

        :param str prop: the SGF property code
        :returns: a list of points for the given property
        """
        if self.node is not None and self.node.has_property(prop):
            return self.node.get(prop)
        else:
            return []

    @property
    def labels(self):
        """Get all labels on the board."""
        return self._get_property('LB')

    @property
    def marks(self):
        """Get all marked stones on the board."""
        return self._get_property('MA')

    @property
    def triangles(self):
        """Get all stones with triangles on the board."""
        return self._get_property('TR')

    @property
    def squares(self):
        """Get all stones with squares on the board."""
        return self._get_property('SQ')

    @property
    def circles(self):
        """Get all stones with circles on the board."""
        return self._get_property('CR')
