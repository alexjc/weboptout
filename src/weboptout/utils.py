## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import os

import atexit
import pickle
import asyncio
import hashlib
import inspect


__all__ = ["allow_async_calls", "cache_to_directory"]


def allow_sync_calls(fn):
    """
    Decorator to allow synchronous programs to use an async-labelled function.
    """
    def _wrapper(*args, **kwargs):
        loop = asyncio._get_running_loop()
        if loop is not None:
            return fn(*args)

        loop = asyncio.new_event_loop()
        atexit.register(loop.close)

        return loop.run_until_complete(fn(*args))
    return _wrapper


def cache_to_directory(directory, /, key: str, filter: callable = None):
    """
    Decorator to cache results of a function to individual pickle files on disk.
    """
    os.makedirs(directory, exist_ok=True)

    def _decorator(fn):
        arg_names = list(inspect.signature(fn).parameters.keys())
        arg_idx = arg_names.index(key)

        assert inspect.iscoroutinefunction(fn), \
            "Synchronous functions not supported by cache_to_directory."

        async def _wrapper(*args, **kwargs):
            hex = hashlib.md5(args[arg_idx].encode()).hexdigest()
            filename = f'{directory}/{hex}.pkl'
            if os.path.isfile(filename):
                result = pickle.load(open(filename, 'rb'))
                if filter is None or not filter(*args, filename=filename, result=result):
                    return result

            result = await fn(*args, **kwargs)
            pickle.dump(result, open(filename, 'wb'))
            return result

        return _wrapper
    return _decorator
