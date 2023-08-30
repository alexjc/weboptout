## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import asyncio
import textwrap

from weboptout import check_domain_reservation, rsv
from weboptout.types import Status


DOMAINS = {
    """Social Media""": None,
    'pinterest.com':    rsv.YES,
    'instagram.com':    rsv.YES,
    'facebook.com':     rsv.YES,
    'twitter.com':      rsv.YES,
    'youtube.com':      rsv.YES,
    'medium.com':       rsv.YES,

    """Stock Photos""": None,
    'photoshelter.com': rsv.YES,
    'smugmug.com':      rsv.YES,
    'istockphoto.com':  rsv.YES,
    'gettyimages.com':  rsv.YES,
    'shutterstock.com': rsv.YES,
    'alamy.com':        rsv.YES,
    'bigstockphoto.com':rsv.YES,

    """Art Platform""": None,
    'artstation.com':   rsv.YES,
    'behance.net':      rsv.YES,
    'deviantart.com':   rsv.MAYBE,
    'etsy.com':         rsv.YES,

    """e-Commerce""":   None,
    'amazon.com':       rsv.YES,
    'aliexpress.us':    rsv.YES,
    'shopify.com':      rsv.YES,
    'ebay.com':         rsv.YES,
    'bigcommerce.com':  rsv.MAYBE,

    """Web Hosting""":  None,
    'wordpress.com':    rsv.MAYBE,
    'squarespace.com':  rsv.MAYBE,

    """News & Media""":   None,
    'dailymail.co.uk':  rsv.YES,
    'cnn.com':          rsv.YES,
    'theguardian.com':  rsv.YES,
    'foxnews.com':      rsv.YES,
    'economist.com':    rsv.YES,
}


def main_synchronous_from_database():
    for domain, expected in DOMAINS.items():
        if expected is None:
            print(f"\n\033[1;97m{domain:22} Opt-Out\033[0m\n")
            continue

        res = check_domain_reservation(domain, use_database=True)
        # assert res == expected, domain
        if res == rsv.YES:
            print(f"  {domain:24}✓")
        else:
            print(f"  {domain:24}?")

        for record in res.process:
            print(
                " ", "\033[92m✓\033[0m" if record[0] == Status.SUCCESS else "\033[91m𐄂\033[0m",
                record[1].value,
                dict(record[2])
            )

        if res == rsv.YES:
            summary = textwrap.wrap(res.outcome[0][1], width=72, initial_indent='   ❝', subsequent_indent='     ')
            print("\n", "\n".join(summary) + "❞")
        print()


async def main_asynchronous_from_network():
    result = await asyncio.gather(*[
        check_domain_reservation(domain, use_database=False)
        for domain, expected in DOMAINS.items() if expected is not None
    ])
    assert len(result) == len(DOMAINS) - 6
    print('\n'.join(map(str, result)))


if __name__ == "__main__":
    main_synchronous_from_database()

    # asyncio.run(main_asynchronous_from_network())
