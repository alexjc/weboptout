## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

from .types import rsv, Status
from .client import ClientSession
from .utils import allow_sync_calls
from .http import search_tos_for_domain
from .html import check_tos_reservation


__all__ = ["check_domain_reservation"]


@allow_sync_calls
async def check_domain_reservation(domain):
    assert not domain.startswith('http://')

    async with ClientSession() as client:
        async for url, tos in search_tos_for_domain(client, domain):

            status = check_tos_reservation(client, url, tos)
            if status == Status.ABORT:
                break
            if status == Status.FAILURE:
                continue

            return rsv.YES(summary=client.log_records[-1][2]['highlight'], records=client.log_records)

    return rsv.MAYBE(summary="", records=client.log_records)
