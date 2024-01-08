## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import sys

import asyncio
import textwrap
import collections

from weboptout import check_domain_reservation, rsv, Status



async def _check_single_domain(lock, domain):
    async with lock:
        print(domain, file=sys.stderr)
        res = await check_domain_reservation(domain)
        return domain, res


async def main(top_k=1000, n_tasks=8):
    # Load list of domains from one or more datasets summaries.
    domains = collections.defaultdict(int)
    for filename in ['data/laion2B-en.tsv', 'data/laion2B-multi.tsv', 'data/laion1B-nolang.tsv']:
        for ln in open(filename, "r").readlines():
            url, count = ln.rstrip('\n').split('\t')
            domains[url] += int(count.split('.')[0].replace(',', ''))

    # Get the top k=100 domains ordered by number of images.
    domains = sorted(domains.items(), key=lambda it: it[1], reverse=True)
    domains = domains[:top_k]
    total = sum(d[1] for d in domains)

    # Gather all the information in parallel tasks.
    sem = asyncio.Semaphore(n_tasks)
    tasks = [_check_single_domain(sem, k) for k, _ in domains]
    result = dict(await asyncio.gather(*tasks))

    print("Domain Name                         Opt-Out              Images\n")
    optout, failed = 0, 0
    total = 0
    for i, (k, v) in enumerate(domains):
        res = result[k]

        if any('lang' in record.context and record.context['lang'] != 'en' for record in res.process):
            continue
        if all('lang' not in record.context for record in res.process):
            continue

        domain, res_name = f"{i+1}) {k}", rsv.get_name(res)
        print(f"{domain:36}{res_name:^8}       {v:12,}")

        total += v
        if res == rsv.YES: optout += v
        if res == rsv.ERROR: failed += v

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

    total -= failed
    print("TOTAL", f"{optout:,}", "opted-out from ", f"{total:,}.", f"(UNAVAILABLE {failed:,})")
    print(optout * 100 / total, '%')


if __name__ == "__main__":
    asyncio.run(main())
