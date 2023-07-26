## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import os
import re
import json
import atexit
import pickle
import asyncio
import difflib
import fnmatch
import hashlib
import inspect
import collections
import pkg_resources

from .types import Reservation


__all__ = [
    "allow_async_calls",
    "limit_concurrency",
    "cache_to_directory",
    "retrieve_result_from_cache"
]


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
    directory = pkg_resources.resource_filename(__name__, directory)
    directory = directory.replace('src/weboptout/', '')
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


def extract_common_pattern(A, B):
    matcher = difflib.SequenceMatcher(a=A, b=B)

    pattern = []
    def push(o):
        if len(pattern) == 0:
            pattern.append(o)

        if pattern[-1] == '𝒊' and o in '𝒊*?':
            pass
        elif pattern[-1] == '𝒅' and o in '𝒅*?':
            pass
        elif pattern[-1] == '*' and o in '*?':
            pass
        else:
            pattern.append(o)

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == 'replace' and (i2-i1) == (j2-j1):
            pattern.append('?' * (i2 - i1))
        elif opcode == 'replace' and (i2-i1) != (j2-j1):
            push('*')
        elif opcode == 'equal' and (i2-i1) == 1:
            pattern.append('?')
        elif opcode == 'equal':
            pattern.append(A[i1:i2])
        elif opcode == 'insert':
            push('𝒊')
        elif opcode == 'delete':
            push('𝒅')
    
    pattern = ''.join(pattern)

    if re.search(r"(𝒊[a-z\.]+𝒅|𝒊[a-z\.]+𝒅)", pattern):
        return None

    pattern = pattern.replace('𝒊', '*').replace('𝒅', '*')
    pattern = re.sub('\*[a-z0-9]\.', '*.', pattern)
    pattern = re.sub('\.[a-z0-9]\*', '.*', pattern)
    pattern = re.sub('[\*\?]*\*[\*\?]*', '*', pattern)

    assert fnmatch.fnmatch(A, pattern), f"{A} didn't match {pattern} as expected."
    assert fnmatch.fnmatch(B, pattern), f"{B} didn't match {pattern} as expected."
    return pattern


def retrieve_result_from_cache(archive, /, key: str, filter: callable = None):
    archive = pkg_resources.resource_filename(__name__, archive)
    archive = archive.replace('src/weboptout/', '')
    os.makedirs(os.path.dirname(archive), exist_ok=True)

    if os.path.isfile(archive):
        lookup = {
            k: Reservation(v[0], v[1], v[2])
            for k, v in pickle.load(open(archive, 'rb')).items()
        }
    else:
        lookup = {}

    def _add_to_database(key, r):
        if r.url is None:
            return

        options = []
        for match in [(k, v) for k, v in lookup.items() if v.url == r.url]:        
            pat = extract_common_pattern(key, match[0])
            if pat is None:
                continue
            options.append((pat, match))

        if len(options) > 0:
            pat, match = options[0]
            lookup[pat] = r
            del lookup[match[0]]
        else:
            lookup[key] = r

    def _dump_to_disk():
        pickle.dump(
            {k: (v._id, v.summary, v.url) for k, v in lookup.items()},
            open(archive, 'wb')
        )
    atexit.register(_dump_to_disk)

    def _decorator(fn):
        arg_names = list(inspect.signature(fn).parameters.keys())
        arg_idx = arg_names.index(key)

        assert inspect.iscoroutinefunction(fn), \
            "Synchronous functions not supported by cache_to_directory."

        async def _wrapper(*args, **kwargs):
            k = args[arg_idx]
            for pattern, result in lookup.items():
                if not fnmatch.fnmatch(k, pattern):
                    continue
                if filter is None or not filter(*args, result=result):
                    return result

            result = await fn(*args, **kwargs)
            _add_to_database(k, result)
            return result

        return _wrapper
    return _decorator
