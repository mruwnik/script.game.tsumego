"""Functions used to download problems from www.goproblems.com"""
import requests
import json
import random
import time
from path import path
from lxml import etree


def parse_problem(html):
    """Parse the given HTML for problem components.

    :param str html: the HTML contents of the problem's page
    :returns: (id, kyu or dan level, the SGF, the problem's rating)
    :raises ValueError: when an error is found in the HTML
    """
    tree = etree.HTML(html)
    error = tree.find('.//div[@class="errorbox"]')
    if error is not None:
        raise ValueError(error.text)

    rating = tree.find('.//a[@id="flag_link"]').text.strip()
    sgf = tree.find('.//div[@id="player-container"]').text.strip()
    difficulty = tree.find('.//div[@class="difficulty"]/a').text.strip().replace(' ', '_')
    problem_id = tree.find('.//div[@class="prob_id"]/a').text.strip()
    return problem_id, difficulty, sgf, rating


def check_directory(checked_dir):
    """Check if the given directory is a directory and ensure it exists.

    If the given path does not exist, it will be created.

    :param path.path checked_dir: the path to the directory
    :raises ValueError: if the path is not a directory
    """
    if not checked_dir.exists():
        checked_dir.makedirs_p()
    elif not checked_dir.isdir():
        raise ValueError('"%s" is not a directory - cannot save the problem in it' % str(checked_dir))
    return checked_dir


def get_problem(base_dir, problem_id, goproblems_url, save_html=False):
    """Get the given problem.

    :param str base_dir: the base dir where the problem is to be saved
    :param int problem_id: the id of the problem to be downloaded
    :param str goproblems_url: the url where the problems can be found
    :param boolean save_html: save the downloaded HTML
    """
    if save_html:
        html_dir = check_directory(path(base_dir) / 'html')
        html_file = html_dir / ('%d.html' % problem_id)
        if html_file.exists():
            print "already downloaded %d" % problem_id
        return False

    response = requests.get(goproblems_url % problem_id)

    if save_html:
        with open(html_file, 'w') as f:
            f.write(response.text)

    if not response.ok:
        raise requests.HTTPError(response.text)

    problem, difficulty, sgf, rating = parse_problem(response.text)

    problem_dir = check_directory(path(base_dir) / difficulty.replace(' ', '_'))

    problem_name = '%s_%s.sgf' % (difficulty, (problem or str(problem_id)))
    if rating:
        problem_name = '[%s]' % rating + problem_name

    with open(problem_dir / problem_name, 'w') as f:
        f.write(sgf)
    return True


def get_newest_id():
    """Get the id of the newest id on the website.

    As the problem ids appear to be incrementing with time, a simple
    way of getting all problems is to get the newest id (which is also
    the highest) and check all numbers from 0 up to that number.
    """
    response = requests.get('http://www.goproblems.com/api/dt_problems.php?iColumns=9&sColumns=id%2C%2Cprobauthorid%2Cprobauthor%2Cgenre%2Celo%2Cdate&iDisplayStart=0&iDisplayLength=1&sSortDir_0=desc')
    try:
        return json.loads(response.text)['aaData'][0][0]
    except (TypeError, ValueError, KeyError) as e:
        print e
        return 0


def download_all_problems(base_dir='problems',
                          base_url='http://www.goproblems.com/%d'):
    """Download all problems from the goproblems.com site.

    The problems will be downloaded to the provided base_dir, sorted
    by difficulty - each kyu or dan level will have it's own directory
    with all problems from that level.

    :param str base_dir: where the problems should be saved
    :param str base_url: the url where the problems can be found
    """
    total_count = get_newest_id()
    for problem_id in xrange(total_count):
        if (problem_id % (total_count / 1000)) == 0:
            print "getting problem {0} of {1} ({2:.2f}% dome)".format(problem_id, total_count, (problem_id * 100.0) / total_count)
        try:
            if get_problem('problems', problem_id, base_url):
                time.sleep(random.randint(1, 2000) / 1000.0)
        except ValueError as e:
            print "couldn't parse problem no. %d: %s" % (problem_id, e.message)
        except AttributeError as e:
            print "couldn't parse problem no. %d: got %r" % (problem_id, e)
        except requests.HTTPError as e:
            print "couldn't parse problem no. %d: html is %s" % (problem_id, e.message)

