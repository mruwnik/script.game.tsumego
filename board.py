#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import choice

from gomill import sgf, sgf_moves


class Goban(object):
    """A representation of a goban."""

    def __init__(self, sgf_string):
        """Initialise the goban from the given SGF string."""
        self.load(sgf_string)

    def load(self, sgf_string):
        """load the given SGF string."""
        self.sgf = sgf_string or ''
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

        The position is counted from the bottom left corner (a cartesian coordinate)."""
        self.node = self._move(self.node, self.next_player, (x, y))

    def back(self):
        """Go back one move, updated the board."""
        if self.node.parent:
            for x, y, player in self.node.diff:
                self.board.board[x][y] = player
            self.node = self.node.parent

    def random_move(self):
        if self.on_path and len(self.node) > 0:
            self.move(*choice(self.node).get_move()[1])

    def __str__(self):
        return '\n'.join("|".join(i if i else ' ' for i in x) for x in reversed(self.board.board))

    @property
    def root(self):
        return self.game.get_root()

    @property
    def current_player(self):
        return self.node.get_move()[0]

    @property
    def next_player(self):
        """Get the next player.

        If the current player is known, then return the other one. If it's
        not known, but the next step is known, return that step's player.
        Otherwise just assume that it's a new game and return black.
        """
        if self.current_player:
            return 'b' if self.current_player == 'w' else 'w'
        elif len(self.node) > 0:
            return self.node[0].get_move()[0]
        else:
            return 'b'

    @property
    def next_player_name(self):
        return 'white' if self.next_player == 'w' else 'black'

    @property
    def current_comment(self):
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

    @property
    def labels(self):
        """Get all labels on the board."""
        return self.root.get('LB') if self.root.has_property('LB') else []


bla = """(;AB[sc]AB[sb]AB[rb]AB[qc]AB[pc]AB[oc]AB[ob]AB[oa]AW[na]AW[nb]AW[nc]AW[od]AW[nd]AW[pd]AW[qd]AW[rd]AW[rc]AW[sd]AB[qb]AW[pb]AW[qa]AW[ra]C[How many ko threats can White make?FORCE]LB[lb:1]LB[la:0]LB[lc:2]LB[ld:3]AP[goproblems]
(;W[la]C[Nope, there's at least one.])
(;W[lb];B[ld]C[Show me]
(;W[sa];B[pa]C[You could've had more...])
(;W[pa];B[sa]C[You've got another ko threat...]))
(;W[lc];B[lb]C[Show me]
(;W[pa];B[sa]
(;W[qa];B[pa]C[Right on!RIGHT])
(;W[pa];B[qa]C[Right on!RIGHT]))
(;W[sa];B[pa]C[You indeed had 2 ko threats, but you played the wrong move.]))
(;W[ld]C[Not quite that many...]))"""
ble = """(;AB[ab]AB[bb]AB[cc]AB[dc]AB[eb]AW[ba]AW[bc]AW[bd]AW[cd]AW[dd]AW[ed]AW[fc]AW[gc]AW[hb]AW[ic]AP[goproblems]
(;B[da];W[ca]
(;B[cb]C[RIGHT];W[ec]
(;B[aa]C[RIGHT])
(;B[fb];W[fa]
(;B[ga];W[gb];B[ea]C[RIGHT])
(;B[aa]C[RIGHT])))
(;B[fb];W[cb];B[db];W[fa]C[]))
(;B[fb];W[cb];B[db];W[ca];B[da];W[fa]C[])
(;B[cb];W[da]
(;B[ea];W[ca];B[ec]C[RIGHT])
(;B[ca];W[ea];B[fb];W[fa];B[ga];W[gb];B[db]C[RIGHT]))
(;B[ca];W[da]
(;B[aa];W[ea]
(;B[fa];W[fb];B[db]C[RIGHT])
(;B[fb];W[fa];B[ga]C[RIGHT]))
(;B[cb];W[ea]
(;B[fb];W[fa];B[ga];W[gb];B[db]C[RIGHT])
(;B[fa];W[fb];B[db];W[ea]C[]))))"""

