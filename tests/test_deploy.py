import pytest

from deploy import tmp, copy, clean


@pytest.yield_fixture
def temp():
    with tmp() as temp:
        yield temp


def test_tmp():
    """Check whether the tmp context manager works correctly."""
    with tmp() as temp:
        assert temp.exists()
        assert temp.isdir()
    assert not temp.exists()


def test_copy(temp):
    """Check whether copying works correctly."""
    test_dir = temp / 'test_dir'
    test_dir.makedirs_p()
    for i in xrange(10):
        (temp / ('test_file_%d' % i)).touch()
        (test_dir / ('test_file_%d' % i)).touch()

    existing_files = ['test_file_%d' % i for i in xrange(4, 10)]
    missing_files = ['test_file_%d' % i for i in xrange(10, 14)]
    files_to_copy = existing_files + missing_files + [test_dir.basename()]

    with tmp() as dest:
        copy(files_to_copy, temp, dest)

        # check whether files that existed were copied
        for filename in existing_files:
            assert (dest / filename).exists()

        # make sure that files that didn't exist don't get created
        for filename in missing_files:
            assert not (dest / filename).exists()

        # check whether directories are correctly copied
        dest_test_dir = dest / test_dir.basename()
        assert dest_test_dir.exists()
        assert dest_test_dir.isdir()
        for f in test_dir.walk():
            assert (dest_test_dir / f.basename()).exists()


def test_clean(temp):
    """Check whether cleaning works."""
    test_dir = temp / 'test_dir'
    test_dir.makedirs_p()
    for filename in ['bla', 'bla.py', 'bla.pyo', 'bla.pyc', 'bla~']:
        (temp / filename).touch()
        (test_dir / filename).touch()

    clean(temp)

    for filename in ['bla', 'bla.py']:
        assert (temp / filename).exists()
        assert (test_dir / filename).exists()

    for filename in ['bla.pyo', 'bla.pyc', 'bla~']:
        assert not (temp / filename).exists()
        assert not (test_dir / filename).exists()

