import os

from xbmc import LOGDEBUG, LOGNOTICE, LOGERROR, LOGSEVERE, LOGFATAL, log as xbmc_log
import xbmcaddon

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')


STRINGS = {
    'show_solution': 32002,
    'hide_solution': 32003,
    'off_path': 32015,
    'solved': 32016,
    'exit_head': 32009,
    'exit_text': 32012,
    'current_rank': 32013,
    'rating': 32014,
    'no_problems_found': 32020,
    'get_problems_dir': 32021,
}


def _(string_id):
    if string_id in STRINGS:
        return addon.getLocalizedString(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id, LOGDEBUG)
        return string_id


def log(msg, level=LOGNOTICE):
    xbmc_log('[ADDON][%s] %s' % (ADDON_NAME, msg.encode('utf-8')), level=level)

