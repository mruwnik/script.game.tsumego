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
            'level': (int(results['level']), results['type']),
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
        problems = self.problems[level]
        return choice(problems)

    def get_rank(self, level):
        """Get the rank for the given level."""
        return (int(math.ceil(abs(level))), 'kyu' if level > 0 else 'dan')

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

    def failure(self, level, scale=0.1):
        """Notify that the player failed a problem."""
        magnitude = (level - self.level + self.level_span + 1) * scale
        self.offset += magnitude
        self.update_rank()

    def success(self, level, scale=0.1):
        """Notify that the player solved a problem."""
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

