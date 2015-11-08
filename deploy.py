#!/usr/bin/python
# -*- coding: utf-8 -*-

import zipfile
from contextlib import contextmanager
from tempfile import mkdtemp
from path import path


PROJECT_FILES = [
    'LICENSE.txt', 'addon.xml', 'game.py', 'icon.png', 'resources',
    'README.md', 'changelog.txt',
]


@contextmanager
def tmp():
    """Get a temporary directory which will be removed after being used."""
    temp = path(mkdtemp())
    yield temp
    temp.rmtree_p()


def copy(files, source, dest):
    """Copy the given files from the given source to the given destination.

    Both directories and normal files will be copied. If a given file doesn't
    exist, it will be skipped. If the destination directory doesn't exist, it
    will be created.

    :param list files: a list of filenames (basenames, not paths) to be copied
    :param path.path source: the directory contining the files
    :param path.path dest: where the files should be copied to
    """
    dest.makedirs_p()
    for filename in files:
        try:
            f = source / filename
            if not f.exists():
                continue
            elif f.isdir():
                f.copytree(dest / filename)
            elif f.isfile():
                f.copy(dest)
        except OSError:
            pass


def clean(directory):
    """Remove all python compiled objects and tmp files from the given dir."""
    map(lambda f: f.remove(), directory.walkfiles('*.py[co]'))
    map(lambda f: f.remove(), directory.walkfiles('*~'))

    # these need to be deleted this way, otherwise the generator raises an
    # OSError because it can't find the deleted object.
    caches = [f for f in directory.walkdirs('__pycache__')]
    for f in caches:
        f.rmtree_p()


def zip_file(to_zip, zip_name):
    """Zip the given file without compression.

    If a directory is specified, it will be recursively zipped.

    :param path.path to_zipped: what is to be zipped
    :param str zip_name: the name of the resulting archive
    """
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_STORED) as zf:
        for f in to_zip.walk():
            zf.write(f, to_zip.relpathto(f))


def make_package(package_name):
    """Make a package out of the directory where this script resides.

    :param str package_name: the name of the resulting package
    """
    with tmp() as temp:
        repo = path(__file__).parent

        copy(PROJECT_FILES, repo, temp / package_name)
        clean(temp)
        zip_file(temp, '%s.zip' % package_name)


make_package('script.game.tsumego')

