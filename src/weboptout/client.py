## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import atexit
import aiohttp
import collections

from . import __version__


LogRecord = collections.namedtuple("LogRecord", ["level", "message", "extras"])


class ClientSession(aiohttp.ClientSession):

    DEFAULT_HEADERS = {
        "Accept-Language": "en",
        "User-Agent": "WebOptOut/"+__version__,
        "X-Forwarded-For": "8.8.8.8"
    }

    def __init__(self):
        timeout = aiohttp.ClientTimeout(connect=5.0, total=10.0)
        super().__init__(timeout=timeout, headers=self.DEFAULT_HEADERS)
        self.log_records = []

    def log(self, level, message, **kwargs):
        self.log_records.append(LogRecord(level, message, kwargs))


def instantiate_webdriver(__singleton__ = []):
    """
    Launch a single instance of Firefox in the background and close it before exiting Python.
    """
    if len(__singleton__) == 1:
        return __singleton__[0]

    from selenium import webdriver
    options = webdriver.FirefoxOptions()
    options.headless = True
    
    wdf = webdriver.Firefox(options=options)
    wdf.set_page_load_timeout(5.0)
    atexit.register(wdf.quit)

    __singleton__.append(wdf)
    return wdf
