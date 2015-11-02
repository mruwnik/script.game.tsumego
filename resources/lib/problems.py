import re
import math
from path import path
from random import choice


class Problems(object):
    """A class to handle a load of problems."""
    level_span = 3
    id_regex = '(?P<id>\d+)'
    level_regex = '(?P<level>\d+)_?(?P<type>kyu|dan)'
    rating_regex = '(?:\[(?P<rating>[+-]?\d+)\])'
    name_parser = re.compile('{rating}?{level}_?{id}.sgf'.format(
        rating=rating_regex,
        level=level_regex,
        id=id_regex,
    ))

    def __init__(self, problems_dir='./', level=30):
        self.problems_dir = path(problems_dir)
        self.level = level
        self.offset = 0
        self.problems = {
            self._parse_level(d.basename()): self._get_problems(d)
            for d in self.problems_dir.listdir()
        }

    def _parse_problem(self, problem_file):
        """Parse the given problem file name.

        :param str problem_file: the filename to be parsed
        :returns: the parts that make up the name
        """
        result = self.name_parser.search(problem_file)
        if not result:
            return
        results = result.groupdict()
        return {
            'rating': int(results['rating']) if results['rating'] else 0,
            'rank': (int(results['level']), results['type']),
            'id': int(results['id']),
            'problem_file': problem_file,
        }

    def _parse_level(self, level_str):
        """Parse the given rank name.

        :param str level_str: the rank name to be parsed
        :returns: a (rank number, rank type) tuple. The number is an int, the \
            type is either 'kyu' or 'dan'
        """
        try:
            value, level_type = level_str.strip().split('_')
            return (int(value), level_type)
        except ValueError:
            return None

    def _get_problems(self, problem_dir):
        """Get all problems from the given directory.

        :param path.path problem_dir: a directory with problems
        """
        try:
            return filter(
                None, map(self._parse_problem, problem_dir.listdir())
            )
        except OSError:
            return None

    def random_problem(self, level=None):
        """Get a random problem for the given level.

        :param tuple level: the level for which a problem should be returned
        """
        if not level:
            level = self.get_rank(round(self.level + self.offset))
        if level[0] > 30:
           level = (30, level[1])
        problems = self.problems[level]
        return choice(problems)

    def get_rank(self, level):
        """Get the rank for the given level."""
        return (int(math.ceil(abs(level))), 'kyu' if level > 0 else 'dan')

    def get_level(self, rank):
        """Get the level for the given rank."""
        return rank[0] if rank[1] == 'kyu' else -rank[0]

    @property
    def rank(self):
        """Get the current rank."""
        return self.get_rank(self.level)

    def update_rank(self):
        """Update the rank based on how well the player is doing."""
        abs_offset = abs(self.offset)
        if abs_offset > self.level_span:
            sign = self.offset / abs_offset
            self.level += int(sign * (math.ceil(abs_offset - self.level_span)))
            self.offset = 0
        return (self.level, self.offset)

    def failure(self, rank, scale=0.1):
        """Notify that the player failed a problem."""
        level = self.get_level(rank)
        magnitude = (level - self.level + self.level_span + 1) * scale
        self.offset += magnitude
        self.update_rank()

    def success(self, rank, scale=0.1):
        """Notify that the player solved a problem."""
        level = self.get_level(rank)
        magnitude = (level - self.level - self.level_span - 1) * scale
        self.offset += magnitude
        self.update_rank()

    def __iter__(self):
        return self

    def next(self):
        """Get the next problem."""
        problem = self.random_problem()
        if not problem:
            raise StopIteration

        with open(problem['problem_file']) as f:
            problem['sgf'] = f.read()
        return problem


class MockProblems(Problems):
    """A mock problem getter to bypass the long loading times of the original."""
    sgf = """(;AB[sc]AB[sb]AB[rb]AB[qc]AB[pc]AB[oc]AB[ob]AB[oa]AW[na]AW[nb]AW[nc]AW[od]AW[nd]AW[pd]AW[qd]AW[rd]AW[rc]AW[sd]AB[qb]AW[pb]AW[qa]AW[ra]C[How many ko threats can White make?FORCE]LB[lb:1]LB[la:0]LB[lc:2]LB[ld:3]AP[goproblems]
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


    def __init__(self, problems_dir='./', level=30):
        self.level = level
        self.offset = 0
        self.problems = {
            self.get_rank(i): [
                self._parse_problem(
                    '%d_%s_%d.sgf' % tuple(list(self.get_rank(i)) + [id_])
                ) for id_ in xrange(i * 10, i * 10 + 10)
            ] for i in xrange(-5, 31)
        }

    def next(self):
        """Get the next problem."""
        problem = self.random_problem()
        if not problem:
            raise StopIteration

        problem['sgf'] = self.sgf
        return problem

