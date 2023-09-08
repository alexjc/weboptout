## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import re
import textwrap

import click

from weboptout import check_domain_reservation, check_url_reservation, rsv
from weboptout.types import Status


@click.group()
def main():
    pass


def _run_checks(check_fn, sources):
    for source in sources:
        res = check_fn(source)
        if res == rsv.YES:
            print(f"  {source:23} ✓")
        else:
            print(f"  {source:23} ?")

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


@main.command()
@click.argument('domains', nargs=-1)
def check_domain(domains):
    print(f"\n\033[1;97m{'Domain':22} Opt-Out\033[0m\n")
    return _run_checks(check_domain_reservation, domains)


@main.command()
@click.argument('urls', nargs=-1)
def check_url(urls):
    print(f"\n\033[1;97m{'Link':22} Opt-Out\033[0m\n")
    return _run_checks(check_url_reservation, urls)


@main.command()
@click.argument('sources', nargs=-1)
def check(sources):
    if all(re.match("^https?://", src) for src in sources):
        return check_url(sources)
    if all(not re.match("^https?://", src) for src in sources):
        return check_domain(sources)
    raise NotImplementedError


if __name__ == "__main__":
    main()
