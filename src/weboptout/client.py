## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import aiohttp

from . import __version__


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
        self.log_records.append((level, message, kwargs))
