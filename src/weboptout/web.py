## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

from .types import rsv, Reservation, Status
from .client import ClientSession
from .utils import allow_sync_calls
from .http import search_tos_for_domain
from .html import check_tos_reservation


__all__ = ["check_domain_reservation"]


@allow_sync_calls
async def check_domain_reservation(domain: str) -> Reservation:
    assert not domain.startswith('http://')

    async with ClientSession() as client:
        async for url, tos, options in search_tos_for_domain(client, domain):
            status = check_tos_reservation(client, url, tos)

            if status == Status.RETRY:
                options.retry = True
                continue

            if status == Status.ABORT:
                return rsv.MAYBE(summary=None, url=url, records=client.log_records)

            if status == Status.FAILURE:
                continue

            return rsv.YES(
                summary=client.log_records[-1][2]["highlight"],
                url=url,
                records=client.log_records,
            )

    # This happens when none of the domains can be looked up.
    return rsv.ERROR(summary=None, records=client.log_records)
