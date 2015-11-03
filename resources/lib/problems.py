import re
import math
import thread
from random import choice

from path import path


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
        self.problems_thread = thread.start_new_thread(
            self._find_problems, (problems_dir,))
        self.problems = None

    def _find_problems(self, problems_dir):
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
        if self.problems:
            problems = self.problems[level]
            return choice(problems)
        else:
            problems_dir = path(self.problems_dir) / ('%d_%s' % level)
            problem = choice(problems_dir.listdir())
            return self._parse_problem(problem)

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

    sgf1 = """(;AW[br]AW[bq]AW[cq]AW[dq]AW[er]AW[fr]AW[ds]AB[ap]AB[bp]AB[cp]AB[dp]AB[ep]AB[eq]AB[fq]AB[gq]AB[gr]AB[gs]AB[fs]AB[es]AB[aq]AW[ar]LB[as:a]LB[bs:b]LB[cr:c]LB[dr:d]LB[cs:e]C[FORCE]AP[goproblems]
(;B[as]LB[dr:a]C[FORCE];W[dr]LB[bs:a]LB[cs:b]C[FORCE]
(;B[bs]LB[cs:a]C[FORCE];W[cs])
(;B[cs]LB[bs:a]C[FORCE];W[bs]))
(;B[bs]LB[cs:a]LB[dr:b]C[FORCE]
(;W[cs]LB[cr:a]LB[dr:b]C[FORCE]
(;B[cr]LB[dr:a]C[FORCE];W[dr])
(;B[dr]C[RIGHT]))
(;W[dr]LB[as:a]LB[cr:b]LB[cs:c]C[FORCE]
(;B[as]LB[cs:a]C[FORCE];W[cs])
(;B[cr]LB[cs:a]C[FORCE];W[cs])
(;B[cs]C[RIGHT])))
(;B[cr]LB[dr:a]C[FORCE];W[dr]LB[bs:a]LB[cs:b]C[FORCE]
(;B[bs]LB[cs:a]C[FORCE];W[cs])
(;B[cs]LB[bs:a]C[FORCE];W[bs]))
(;B[dr]C[RIGHT])
(;B[cs]LB[bs:a]LB[cr:b]LB[dr:c]C[FORCE]
(;W[bs]LB[cr:a]LB[dr:b]C[FORCE]
(;B[cr]LB[dr:a]C[FORCE];W[dr])
(;B[dr]C[RIGHT]))
(;W[cr]LB[as:a]LB[bs:b]LB[dr:c]C[FORCE]
(;B[as]LB[bs:a]C[FORCE];W[bs]LB[dr:a]C[FORCE];B[dr]LB[er:a]C[FORCE];W[er]LB[fr:a]C[FORCE];B[fr]LB[dr:a]C[FORCE];W[dr])
(;B[bs]C[RIGHT])
(;B[dr]C[RIGHT]))
(;W[dr]LB[as:a]LB[bs:b]LB[cr:c]C[FORCE]
(;B[as]LB[bs:a]C[FORCE];W[bs])
(;B[bs]C[RIGHT])
(;B[cr]LB[bs:a]C[FORCE];W[bs]))))"""

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

        problem['sgf'] = self.sgf1
        return problem


