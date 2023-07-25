## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import os

import json
import atexit
import pickle
import asyncio
import fnmatch
import hashlib
import inspect
import collections
import pkg_resources


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


def limit_concurrency(value: int):
    """
    Decorator to prevent an async function from being called more than N times.
    """
    semaphore = asyncio.Semaphore(value)
    def _decorator(fn):
        async def _wrapper(*args, **kwargs):
            async with semaphore:
                return await fn(*args, **kwargs)
        _wrapper.__wrapped__ = fn
        return _wrapper
    return _decorator


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

        _wrapper.__wrapped__ = fn
        return _wrapper
    return _decorator


def retrieve_from_database(archive, /, key: str, filter: callable = None):
    Entry = collections.namedtuple('Entry', ['pattern', 'url'])

    archive = pkg_resources.resource_filename(__name__, archive)
    archive = archive.replace('src/weboptout/', '')

    if os.path.isfile(archive):
        with open(archive, 'r') as f:
            assert f.readline().startswith("## Copyright")
            database = [Entry(*json.loads(e)) for e in f.readlines()]
    else:
        database = []

    def _decorator(fn):
        arg_names = list(inspect.signature(fn).parameters.keys())
        arg_idx = arg_names.index(key)

        assert inspect.iscoroutinefunction(fn), \
            "Synchronous functions not supported by retrieve_from_database."

        async def _wrapper(*args, **kwargs):
            k = args[arg_idx].replace('https://', '')
            for entry in database:
                if not fnmatch.fnmatch(k, entry.pattern):
                    continue
                if filter is None or not filter(*args, result=result):
                    return args[arg_idx], [entry.url]

            result = await fn(*args, **kwargs)
            return result

        return _wrapper
    return _decorator
