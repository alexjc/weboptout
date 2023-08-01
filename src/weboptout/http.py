## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import asyncio
import aiohttp
import warnings
import itertools
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import RE_HREF_TOS, RE_TEXT_TOS
from .utils import cache_to_directory, retrieve_from_database, limit_concurrency
from .client import instantiate_webdriver
from .steps import Steps as S


__all__ = ["search_tos_for_domain"]


def _log_cache_hit(client, url, /, filename, result):
    with client.setup_log() as report:
        report(S.RetrieveContent, succeed=bool(result[-1] not in ("", None)), cache=filename, url=url)


@cache_to_directory("cache/www", key="url", filter=_log_cache_hit)
async def _fetch_from_cache_or_network(client, url: str) -> tuple:
    try:
        async with client.get(url) as response:
            # Add dict(response.headers) to context
            # Add response.url to context.

            html = ""

            with client.setup_log() as report:
                report(S.ResolveDomain, success=True, domain=response.url.host)
                report(S.EstablishConnection, success=True, address=response.connection.transport.get_extra_info('peername') if response.connection else '')

                report(S.RetrieveContent, success=bool(response.status == 200), status_code=response.status, url=url)

                report(
                    S.ValidateContentFormat,
                    content_type=(content_type := response.headers.get("Content-Type", "")),
                    fail=any(t in content_type for t in ("application/", "image/")),
                )

                try:
                    html = await response.text()
                except UnicodeDecodeError as exc:
                    report(S.ValidateContentEncoding, fail=True, exception=str(exc))

                report(S.ValidateContentLength, fail=len(html) == 0, bytes=len(html))

            return str(response.url), dict(response.headers), html

    except asyncio.exceptions.TimeoutError as exc:
        with client.setup_log() as report:
            report(S.ResolveDomain, fail=True, exception=str(exc))

    except aiohttp.ClientError as exc:
        with client.setup_log() as report:
            report(S.EstablishConnection, fail=True, exception=str(exc))

    except AssertionError as exc:
        with client.setup_log() as report:
            report(S.EstablishConnection, fail=True, exception=str(exc))

    return url, {}, None


@retrieve_from_database("data/tos.jsonl", key="url")
async def _find_tos_links_from_url(client, url: str) -> list[str]:
    url, _, html = await _fetch_from_cache_or_network(client, url)

    if html is None:
        return None, None

    if html == "":
        return url, None

    return await _find_tos_links_from_html(client, url, html)


async def _find_tos_links_from_html(client, url, html: str) -> list[str]:
    with warnings.catch_warnings(record=True) as w:
        soup = BeautifulSoup(html, "html.parser")
    
    with client.setup_log() as report:
        links = []
        report(S.ParsePage, fail=len(w) > 0, url=url, **{'html': html, 'warnings': w} if len(w) > 0 else {})

        all_links = [
            l
            for l in soup.find_all("a")
            if l.get("href") is not None
            and not (href := l.get("href")).lower().startswith("javascript:")
            and not any(href.startswith(k) for k in "#?")
            and not (l.get_text().lower in ["refresh", "reload"])
        ]

        report(S.ValidatePageLinks,
               fail=bool(len(all_links) == 0),
               filtered_count=len(all_links),
               original_count=len(soup.find_all("a")),
        )

        match_links, match_texts = [], []
        for link in all_links:
            if RE_HREF_TOS.search(str(link.get("href"))):
                match_links.append(link)
            if RE_TEXT_TOS.search(str(link.get_text()).strip()):
                match_texts.append(link)

        match_texts = sorted(match_texts, key=lambda l: len(l.get_text()))
        match_links = sorted(match_links, key=lambda l: len(l.get("href")))

        report(
            S.FindSomeLinksToTerms,
            fail=not match_links and not match_texts
        )

        links = [
            urljoin(url, link.get("href"))
            for link in sorted(
                set(match_texts) & set(match_links),
                key=lambda l: len(l.get("href"))
            )
        ]

        report(
            S.FindGoodLinksToTerms,
            succeed=len(links) > 0
        )

        def valid_link(url):
            return not any(k in url for k in ["login", "privacy", "signup", "user/", "users/", "tags/", "categories/"])

        links = [
            urljoin(url, l.get("href"))
            for p in itertools.zip_longest(match_links, match_texts)
            for l in p
            if (l is not None and valid_link(l.get("href")))
        ]

    return url, links


def _reject_if_header_missing(url, headers, /, filename, result):
    return "User-Agent" not in headers
    

@cache_to_directory("cache/www", key="url", filter=_reject_if_header_missing)
@limit_concurrency(value=1)
async def _fetch_from_browser_then_cache_result(url, headers):
    try:
        webdriver = instantiate_webdriver()
        await webdriver.open_tab(url)
    except Exception as exc: # selenium.common.exceptions.TimeoutException
        await webdriver.close_tab()
        if "Message: Navigation timed out after" not in str(exc):
            raise
        return url, headers, ""

    for i in range(100):
        if not (await webdriver.is_page_loading(url)):
            break
        await asyncio.sleep(0.05)
    await asyncio.sleep(2.0)

    html = await webdriver.get_page_html()
    headers["User-Agent"] = "WebOptOut/Firefox"
    await webdriver.close_tab()

    return url, headers, html


@dataclass
class RequestOptions:
    retry: bool = False


async def search_tos_for_domain(client, domain: str, attempts: int = 4) -> str:
    assert not any(domain.startswith(k) for k in ("https://", "http://"))

    # Step 1) find the right domain from the domain.
    while domain.count(".") > 0:
        links = []
        url, links = await _find_tos_links_from_url(client, "https://" + domain)

        if url is None or len(links or []) == 0:
            domain = ".".join(domain.split(".")[1:])
            continue
        else:
            break

    # No data from server, just terminate.
    if links is None:
        return

    # Content received but no links.
    if len(links) == 0:
        yield url, "", {}
        return

    # Step 2) find the right page on that domain, maximum four tries.
    visited = set()
    while len(links) > 0 and len(visited) < attempts:
        url = links.pop(0)
        visited.add(url)

        new_url, headers, html = await _fetch_from_cache_or_network(client, url)
        if html is None:
            continue

        options = RequestOptions()
        yield new_url, html, options

        if options.retry:
            url, headers, html = await _fetch_from_browser_then_cache_result(url, headers)
            yield url, html, options

        url, further_links = await _find_tos_links_from_html(client, url, html)
        links.extend(l for l in further_links if l not in links and l not in visited)
