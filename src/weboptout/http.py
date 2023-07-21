## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import asyncio
import aiohttp
import itertools
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .utils import cache_to_directory
from .types import Status
from .config import RE_HREF_TOS, RE_TEXT_TOS


__all__ = ["search_tos_for_domain"]


def _log_cache_hit(client, url, /, filename, result):
    client.log(Status.SUCCESS, f"Loaded data for {url} from {filename}")


@cache_to_directory("./cache/www", key="url", filter=_log_cache_hit)
async def _fetch_from_cache_or_network(client, url: str) -> tuple:
    try:
        async with client.get(url) as response:
            if response.headers.get("Content-Type", "").startswith("image/"):
                client.log(
                    Status.FAILURE,
                    f"Response contains binary content where text/* was expected "
                    f"from {url}",
                    headers=dict(response.headers),
                )
                return str(response.url), dict(response.headers), ""

            if response.status != 200:
                client.log(
                    Status.FAILURE,
                    f"An HTTP error code {response.status} was returned from {url}; "
                    f"trying to proceed anyway...",
                    headers=dict(response.headers),
                )

            html = await response.text()
            if response.status == 200:
                client.log(
                    Status.SUCCESS,
                    f"The HTTP request (code {response.status}) from {url} "
                    f"returned {len(html):,} bytes.",
                    headers=dict(response.headers),
                )
            return str(response.url), dict(response.headers), html

    except asyncio.exceptions.TimeoutError as exc:
        client.log(
            Status.FAILURE,
            f"Timeout from HTTP client while resolving {url} server(s).",
            exception=exc,
        )
    except aiohttp.ClientError as exc:
        client.log(
            Status.FAILURE,
            f"Problem with HTTP client while connecting to {url} server(s).",
            exception=exc,
        )

    return url, {}, ""


async def _find_tos_links_from_url(client, url: str) -> list[str]:
    url, _, html = await _fetch_from_cache_or_network(client, url)
    if html == "":
        client.log(
            Status.FAILURE, f"Couldn't find ToS links as there's no data from {url}"
        )
        return url, []

    return await _find_tos_links_from_html(client, url, html)


async def _find_tos_links_from_html(client, url, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")

    all_links = [
        l
        for l in soup.find_all("a")
        if l.get("href") is not None
        and not (href := l.get("href")).startswith("#")
        and not href.lower().startswith("javascript:")
    ]
    if len(all_links) == 0 or any(
        k in html for k in ("turn on javascript", "enable-javascript.com")
    ):
        client.log(
            Status.FAILURE, f"JavaScript must be enabled to view content from {url}"
        )
        return url, []

    match_links, match_texts = [], []
    for link in all_links:
        if RE_HREF_TOS.search(str(link.get("href"))):
            match_links.append(link)
        if RE_TEXT_TOS.search(str(link.get_text()).strip()):
            match_texts.append(link)

    match_texts = sorted(match_texts, key=lambda l: len(l.get_text()))
    match_links = sorted(match_links, key=lambda l: len(l.get("href")))

    if not match_links and not match_texts:
        client.log(
            Status.FAILURE,
            f"No matching links found from {len(all_links)} in ToS at {url}",
        )
        return url, []

    match_both = set(match_texts) & set(match_links)
    if len(match_both) > 0:
        client.log(
            Status.SUCCESS,
            f"Found {len(match_both)} obvious ToS link(s) "
            f"from {len(match_links)} href matches and {len(match_texts)} "
            f"text matches.",
        )
        match_both = sorted(list(match_both), key=lambda l: len(l.get("href")))
        return url, list(urljoin(url, link.get("href")) for link in match_both)

    client.log(
        Status.SUCCESS,
        f"Found {len(set(match_links)|set(match_texts))} ToS candidate links "
        f"including {len(match_links)} href matches and {len(match_texts)} "
        f"text matches.",
    )

    return url, [
        urljoin(url, l.get("href"))
        for p in itertools.zip_longest(match_links, match_texts)
        for l in p
        if l is not None
    ]


async def search_tos_for_domain(client, domain: str) -> str:
    assert not domain.startswith("http")

    # Step 1) find the right domain from the domain.
    while domain.count(".") > 0:
        links = []
        url, links = await _find_tos_links_from_url(client, "https://" + domain)

        if len(links) == 0:
            domain = ".".join(domain.split(".")[1:])
            continue
        else:
            break

    if len(links) == 0:
        return

    # Step 2) find the right page on that domain.
    visited = set()
    while len(links) > 0:
        url = links.pop(0)
        visited.add(url)

        url, _, html = await _fetch_from_cache_or_network(client, url)
        if html is None:
            continue

        client.log(
            Status.SUCCESS,
            f"Retrieved Terms Of Service for {url} with {len(html):,} bytes of text.",
        )
        yield url, html

        url, further_links = await _find_tos_links_from_html(client, url, html)
        links.extend(l for l in further_links if l not in links and l not in visited)
