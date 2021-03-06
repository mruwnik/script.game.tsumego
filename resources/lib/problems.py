import re
import math
import thread
import logging
from random import choice

from path import path


class Problems(object):
    """A class to handle a load of problems."""
    level_span = 3
    id_regex = '(?P<id>\d+)'
    level_regex = '(?P<level>\d+)[_ ]*?(?P<type>kyu|dan)'
    rating_regex = '(?:\[(?P<rating>[+-]?\d+)\])'
    name_parser = re.compile('{rating}?{level}_?{id}.sgf'.format(
        rating=rating_regex,
        level=level_regex,
        id=id_regex,
    ))
    level_parser = re.compile(level_regex)

    def __init__(self, problems_dir='./', level='30 kyu'):
        self.problems_dir = path(problems_dir)
        self.offset = 0
        self.problems_thread = thread.start_new_thread(
            self._find_problems, (problems_dir,))
        self.problems = None
        self.level = self.get_level(self._parse_level(level))

    def _find_problems(self, problems_dir):
        """Find all problems in the problems directory."""
        problems = {}
        for d in self.problems_dir.listdir():
            try:
                level = self._parse_level(d.basename())
                self.problems[level] = self._get_problems(d)
            except OSError:
                continue
        self.problems = problems

    def _parse_problem(self, problem_file):
        """Parse the given problem file name.

        If the name cannot be parsed, only the file bit is returned.

        :param str problem_file: the filename to be parsed
        :returns: the parts that make up the name + the file
        """
        if not (problem_file and problem_file.endswith('.sgf')):
            return

        result = self.name_parser.search(problem_file)
        if not result:
            return {'problem_file': problem_file}
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
            results = self.level_parser.search(level_str).groupdict()
            return (int(results['level']), results['type'])
        except (ValueError, KeyError, AttributeError):
            logging.warning('Could not parse %s: bad level format', level_str)
            return None

    def _get_problems(self, problem_dir):
        """Get all problems from the given directory.

        :param path.path problem_dir: a directory with problems
        """
        rank = self._parse_level(problem_dir.basename())
        problems = []
        for problem in problem_dir.listdir():
            try:
                problem_dict = self._parse_problem(problem)
                if 'rank' not in problem_dict:
                    problem_dict['rank'] = rank
            except (OSError, TypeError):
                logging.info('Could not get any problems from %s', problem)
            else:
                problems.append(problem_dict)
        return problems

    def random_problem(self, level=None):
        """Get a random problem for the given level.

        :param tuple level: the level for which a problem should be returned
        """
        if not level:
            level = self.get_rank(round(self.level + self.offset))
        if level[0] > 30:
            level = (30, level[1])
        try:
            if self.problems:
                problem = choice(self.problems[level])
            else:
                problems_dir = path(self.problems_dir) / ('%d_%s' % level)
                problem = self._parse_problem(choice(problems_dir.listdir()))
        except (OSError, IOError, KeyError):
            return None

        try:
            with open(problem['problem_file']) as f:
                problem['sgf'] = f.read()
        except IOError:
            return None

        # make sure that the SGF can be solved
        if 'RIGHT' not in problem['sgf']:
            return None

        return problem

    def get_rank(self, level):
        """Get the rank for the given level."""
        rank_value = min(30, int(math.ceil(abs(level))))
        return (rank_value, 'kyu' if level > 0 else 'dan')

    def get_level(self, rank):
        """Get the level for the given rank."""
        return rank[0] if rank[1] == 'kyu' else -rank[0]

    @property
    def rank(self):
        """Get the current rank."""
        return self.get_rank(self.level)

    @property
    def pretty_rank(self):
        """Get the current rank in a pretty format."""
        return '%d %s' % self.rank

    def update_rank(self):
        """Update the rank based on how well the player is doing."""
        abs_offset = abs(self.offset)
        if abs_offset > self.level_span:
            sign = self.offset / abs_offset
            self.level += int(sign * (math.ceil(abs_offset - self.level_span)))
            self.offset = 0
        return (self.level, self.offset)

    def failure(self, rank, scale=0.25):
        """Notify that the player failed a problem."""
        level = self.get_level(rank)
        magnitude = (level - self.level + self.level_span + 1) * scale
        self.offset += magnitude
        self.update_rank()

    def success(self, rank, scale=0.25):
        """Notify that the player solved a problem."""
        level = self.get_level(rank)
        magnitude = (level - self.level - self.level_span - 1) * scale
        self.offset += magnitude
        self.update_rank()

    def __iter__(self):
        return self

    def next(self):
        """Get the next problem.

        If no probelems are available for the current level, it will try 3
        ahead and 3 behind for something.
        """
        levels = range(self.level, self.level + 3)
        levels += range(self.level, self.level - 3, -1)
        for level in levels:
            problem = self.random_problem(
                self.get_rank(round(level + self.offset))
            )
            if problem:
                break
        if not problem:
            raise StopIteration

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

    sgf1 = """(;AW[br]AW[bq]AW[cq]AW[dq]AW[er]AW[fr]AW[ds]AB[ap]AB[bp]AB[cp]AB[dp]AB[ep]AB[eq]AB[fq]AB[gq]AB[gr]AB[gs]AB[fs]AB[es]AB[aq]AW[ar]LB[aq:b]LB[ar:w]LB[as:a]LB[bs:b]LB[cr:c]LB[dr:d]LB[cs:e]C[FORCE]AP[goproblems]
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

    sgf2 = """(;AB[cr]AB[dq]AB[eq]AB[er]AB[fr]AW[cq]AW[dp]AW[ep]AW[fp]AW[fq]AW[gr]AW[hq]AW[jq]AB[cn]AB[ck]C[tesuji to connect without ko]AP[goproblems]
(;B[do];W[dn];B[eo];W[en];B[fo];W[fn];B[go];W[gn];B[ho];W[hn];B[io];W[in];B[jo]TR[cn]TR[ck]MA[dn]MA[en]MA[fn]MA[gn]MA[hn]MA[in]MA[fq]MA[hq]MA[jq]TR[go]TR[ho]TR[io]TR[fo]C[rectangulars are strong, triangulars are weak])
(;B[bq];W[bp];B[cp];W[co];B[bo];W[cq]C[instruction : tesuji to connect without ko];B[ap];W[cp];B[bn];W[br];B[aq];W[cs];B[dr];W[fs]C[B is dead. B3 atari underneath is lead to ko.]))
"""
    sgf3 = """(;SZ[11]AB[ce]AB[be]AB[ad]AB[bc]AW[cd]AW[cc]AW[bb]AW[ab]AW[cb]AW[de]AB[bf]AB[bg]AW[df]AB[af]C[W to kill]AP[goproblems]
                                                (;W[bd]C[YES B IS DEAD :)RIGHT])
                                                (;W[ac];B[bd]C[B is alive :(]))"""

    def __init__(self, problems_dir='./', level='30 kyu', **kwargs):
        self.level = self.get_level(self._parse_level(level))
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
        problem = self._parse_problem('[3]_12_kyu_123124.sgf')
        if not problem:
            raise StopIteration

        problem['sgf'] = self.sgf1

        if 'RIGHT' not in problem['sgf']:
            raise StopIteration
        return problem

