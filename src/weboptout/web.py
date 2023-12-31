## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

from urllib.parse import urlparse

from .types import rsv, Reservation, Status
from .client import ClientSession
from .utils import allow_sync_calls
from .http import search_tos_for_domain
from .html import check_tos_reservation


__all__ = ["check_domain_reservation"]


@allow_sync_calls
async def check_domain_reservation(domain: str) -> Reservation:
    assert not any(domain.startswith(k) for k in ("https://", "http://"))

    async with ClientSession() as client:
        async for url, tos, options in search_tos_for_domain(client, domain):
            # No TOS found but at least the server worked.
            if tos == "":
                return rsv.MAYBE(url=url, process=client._steps, outcome=client._output)

            status = check_tos_reservation(client, url, tos)

            # Need to fetch the content again with webdriver?
            if status == Status.RETRY:
                options.retry = True
                continue

            # Wrong place or wrong language from website...
            if status == Status.ABORT:
                return rsv.MAYBE(url=url, process=client._steps, outcome=client._output)

            # Not enough text or not enough legal content.
            if status == Status.FAILURE:
                continue

            return rsv.YES(url=url, process=client._steps, outcome=client._output)

    # This happens when none of the domains can be looked up.
    return rsv.ERROR(url=None, process=client._steps, outcome=client._output)


def check_url_reservation(url: str) -> Reservation:
    domain = urlparse(url).netloc
    return check_domain_reservation(domain)
