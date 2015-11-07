from tempfile import mkdtemp

import pytest
from path import path

from resources.lib.problems import Problems


@pytest.yield_fixture
def problems_dir():
    """A temp directory that will get deleted after the test ends."""
    problems = path(mkdtemp())
    yield problems
    problems.removedirs_p()


@pytest.fixture
def problem_files(problems_dir):
    """A load of dummy problem files."""
    for i in xrange(20):
        (problems_dir / ('%d_kyu_%d.sgf' % (i, i))).touch()
        (problems_dir / ('[%d]%d_kyu_%d.sgf' % (i - 10, i, i + 20))).touch()
        (problems_dir / ('%d.txt' % i)).touch()
        (problems_dir / ('%d.sgf' % i)).touch()
    return problems_dir


@pytest.mark.parametrize('filename, result', (
    ('1_kyu_123.sgf', {'rating': 0, 'rank': (1, 'kyu'), 'id': 123}),
    ('1_kyu123.sgf', {'rating': 0, 'rank': (1, 'kyu'), 'id': 123}),
    ('1kyu_123.sgf', {'rating': 0, 'rank': (1, 'kyu'), 'id': 123}),
    ('13_kyu_123.sgf', {'rating': 0, 'rank': (13, 'kyu'), 'id': 123}),
    ('1_dan_123.sgf', {'rating': 0, 'rank': (1, 'dan'), 'id': 123}),
    ('[+12]1_kyu_123.sgf', {'rating': 12, 'rank': (1, 'kyu'), 'id': 123}),
    ('[12]1_kyu_123.sgf', {'rating': 12, 'rank': (1, 'kyu'), 'id': 123}),
    ('[-1]1_kyu_123.sgf', {'rating': -1, 'rank': (1, 'kyu'), 'id': 123}),
))
def test_parse_problem(filename, result, problems_dir):
    """Test whether filenames get parsed correctly."""
    p = Problems(problems_dir)
    result['problem_file'] = filename
    assert p._parse_problem(filename) == result


@pytest.mark.parametrize('filename',
    ('12_ky_123.sgf', 'kyu_123.sgf', 'asdasd.sgf')
)
def test_unparsable_parse_problem(filename, problems_dir):
    """Check whether names that cannot be parsed only return the filename."""
    p = Problems(problems_dir)
    assert p._parse_problem(filename) == {'problem_file': filename}


@pytest.mark.parametrize('filename',
    (None, '', 'daads', '1_kyu_12.txt', '1_kyu_12')
)
def test_invalid_parse_problem(filename, problems_dir):
    """Check whether invalid names return None."""
    p = Problems(problems_dir)
    assert p._parse_problem(filename) is None


@pytest.mark.parametrize('rank_str, rank', (
    ('12_kyu', (12, 'kyu')),
    ('-12_kyu', (12, 'kyu')),
    ('1_dan', (1, 'dan')),
    ('0_dan', (0, 'dan')),
    ('asd', None),
    ('', None),
))
def test_parse_rank(rank_str, rank, problems_dir):
    """Test whether rank strings are correctly parsed."""
    p = Problems(problems_dir)
    assert p._parse_level(rank_str) == rank


def test_get_problems(problem_files, problems_dir):
    """Check whether problem files are correctly found and returned."""
    p = Problems(problem_files)
    problems = [
        p._parse_problem(problems_dir / ('%d_kyu_%d.sgf' % (i, i)))
        for i in xrange(20)
    ]
    problems += [
        p._parse_problem(
            problems_dir / ('[%d]%d_kyu_%d.sgf' % (i - 10, i, i + 20))
        ) for i in xrange(20)
    ]
    for i in xrange(20):
        problem = {'rank': None}
        problem.update(p._parse_problem(problems_dir / ('%d.sgf' % i)))
        problems.append(problem)

    assert sorted(p._get_problems(problem_files)) == sorted(problems)


@pytest.mark.parametrize('level, rank', (
    (12, (12, 'kyu')),
    (12.12, (13, 'kyu')),
    (22, (22, 'kyu')),
    (0.1, (1, 'kyu')),
    (0, (0, 'dan')),  # this is a corner case
    (-0.1, (1, 'dan')),
    (-10, (10, 'dan')),
))
def test_rank(level, rank, problems_dir):
    """Check whether the rank is correctly calculated."""
    p = Problems(problems_dir)
    p.level = level
    assert p.rank == rank == p.get_rank(level)
    assert p.pretty_rank == '%d %s' % rank


@pytest.mark.parametrize('level, offset, expected', (
    (30, 2, (30, 2)),
    (30, 2.2, (30, 2.2)),
    (30, 3, (30, 3)),
    (30, 3.1, (31, 0)),
    (30, 5.1, (33, 0)),
    (30, 6.1, (34, 0)),
    (30, -3.1, (29, 0)),
    (0, 3.1, (1, 0)),
    (0.12, 3.1, (1.12, 0)),
))
def test_update_rank(level, offset, expected, problems_dir):
    """Check whether updating the rank works correctly."""
    p = Problems(problems_dir)
    p.level = level
    p.offset = offset
    p.update_rank()
    assert expected == (p.level, p.offset)

