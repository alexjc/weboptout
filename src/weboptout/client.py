## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import atexit
import asyncio
import aiohttp
import collections
import concurrent.futures
from contextlib import contextmanager

from . import __version__
from .types import Status


__all__ = ["ClientSession", "instantiate_webdriver"]


class PassThrough(Exception):
    def __init__(self, status, step):
        self.status = status
        self.step = step


LogRecord = collections.namedtuple("LogRecord", ["status", "step", "context"])


class Log:
    """
    Context decorator for logging a step of the analysis.
    """

    def __init__(self, log):
        self.status = Status.ABORT
        self._log = log

    def __call__(self, step,
        # Active codes which force the scope to exit after logging.
        succeed: bool = None, fail: bool = None,
        # Passive codes which record the log and don't exit.
        success: bool = None, failure: bool = None,
        # Extra information to be attached to the log record.
        **context
    ):
        status = Status.SUCCESS if (succeed is True or success is True or fail is False or failure is False) else Status.FAILURE
        self._log.append(LogRecord(status, step, context))
        if succeed is True:
            self.status = Status.SUCCESS
            raise PassThrough(Status.SUCCESS, step)
        if fail is True:
            self.status = Status.FAILURE
            raise PassThrough(Status.FAILURE, step)



class ClientSession(aiohttp.ClientSession):

    DEFAULT_HEADERS = {
        "Accept-Language": "en",
        "User-Agent": "WebOptOut/"+__version__,
        "X-Forwarded-For": "8.8.8.8"
    }

    def __init__(self):
        timeout = aiohttp.ClientTimeout(connect=5.0, total=10.0)
        super().__init__(timeout=timeout, headers=self.DEFAULT_HEADERS)
        self._steps = []
        self._output = []

    @contextmanager
    def setup_log(self):
        log = Log(self._steps)
        try:
            yield log
        except PassThrough as exc:
            assert log.status == exc.status
            assert len(self._steps) > 0
            return True
        finally:
            pass


class WebDriverAsyncWrapper:

    def __init__(self, webdriver):
        self.webdriver = webdriver
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.run_in_thread = asyncio.get_event_loop().run_in_executor
        self.start_window = self.webdriver.current_window_handle

    async def open_tab(self, url):
        self.webdriver.switch_to.new_window('tab')
        return await self.run_in_thread(self.executor, self.webdriver.get, url)

    async def is_page_loading(self, url):
        result = await self._execute_script("return document.readyState")
        return bool(result == "complete")

    async def get_page_html(self):
        return await self._execute_script("return document.documentElement.outerHTML")
    
    async def close_tab(self):
        self.webdriver.close()
        self.webdriver.switch_to.window(self.start_window)

    def _execute_script(self, script):
        return self.run_in_thread(self.executor, self.webdriver.execute_script, script)


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
    wdf.set_page_load_timeout(30.0)
    atexit.register(wdf.quit)

    wdf = WebDriverAsyncWrapper(wdf)
    __singleton__.append(wdf)
    return wdf
