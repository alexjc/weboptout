## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import atexit
import asyncio
import aiohttp
import collections
import concurrent.futures

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
    # options.headless = True
    
    wdf = webdriver.Firefox(options=options)
    wdf.set_page_load_timeout(30.0)
    atexit.register(wdf.quit)

    wdf = WebDriverAsyncWrapper(wdf)
    __singleton__.append(wdf)
    return wdf
