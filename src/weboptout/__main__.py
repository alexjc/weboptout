## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import textwrap

import click

from weboptout import check_domain_reservation, rsv
from weboptout.types import Status


@click.group()
def main():
    pass


@main.command()
@click.argument('domains', nargs=-1)
def check(domains):
    print(f"\n\033[1;97m{'Domain':22} Opt-Out\033[0m\n")

    for domain in domains:
        res = check_domain_reservation(domain, use_database=True)
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


if __name__ == "__main__":
    main()
