## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

from .types import rsv, Reservation, Status
from .client import ClientSession
from .utils import allow_sync_calls, retrieve_result_from_cache
from .http import search_tos_for_domain
from .html import check_tos_reservation


__all__ = ["check_domain_reservation"]


@allow_sync_calls
@retrieve_result_from_cache("cache/rsv.pkl", key="domain")
async def check_domain_reservation(domain: str) -> Reservation:
    assert not any(domain.startswith(k) for k in ("https://", "http://"))

    async with ClientSession() as client:
        async for url, tos, options in search_tos_for_domain(client, domain):
            # No TOS found but at least the server worked.
            if tos == "":
                return rsv.MAYBE(summary=None, url=url, records=client.log_records)

            status = check_tos_reservation(client, url, tos)

            # Need to fetch the content again with webdriver?
            if status == Status.RETRY:
                options.retry = True
                continue

            # Wrong place or wrong language from website...
            if status == Status.ABORT:
                return rsv.MAYBE(summary=None, url=url, records=client.log_records)

            # Not enough text or not enough legal content.
            if status == Status.FAILURE:
                continue

            return rsv.YES(
                summary=client.log_records[-1][2]["highlight"],
                url=url,
                records=client.log_records,
            )

    # This happens when none of the domains can be looked up.
    return rsv.ERROR(summary=None, records=client.log_records)
