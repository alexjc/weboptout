## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import re
import langdetect
from bs4 import BeautifulSoup

from .types import Status
from .config import RE_TDM_CONCEPTS, RE_LEGAL_WORDS, RE_NFP_CONCEPTS


__all__ = ["check_tos_reservation"]


def _find_matching_paragraphs(patterns: list, text: str) -> list[tuple]:
    """
    For each paragraph in the text, apply all the patterns in order and stop when
    there's a match.  The results are sorted by rank of the pattern to find which
    is the most important.
    """
    reasons = []
    for line in text.split("\n"):
        for rank, regexp in enumerate(patterns):
            match = regexp.search(line.rstrip("\n"))
            if not match:
                continue

            i, j = match.start(), match.end() - 1
            while line[i] not in "().;" and i > 0:
                i -= 1
            while line[j] not in "().;" and j + 1 < len(line):
                j += 1

            explain = line[i : j + 1].lstrip("().,; ").rstrip("() ")
            reasons.append((rank, explain, line))
            break

    return sorted(reasons, key=lambda x: x[0] * 1000 - len(x[1]))


def check_tos_reservation(client, url: str, html: str) -> Status:
    soup = BeautifulSoup(html, "html.parser")
    text = "\n".join(_extract_paragraphs(soup))

    para_count = text.count("\n") + 1

    # Only english language is currently supported.
    if len(text) > 1_000 and (lang := langdetect.detect(text)) != "en":
        client.log(
            Status.FAILURE,
            f"Found a possible ToS page but language is '{lang.upper()}' at {url}",
        )
        return Status.ABORT

    # Words that match data-mining concepts.
    if len(reasons := _find_matching_paragraphs(RE_TDM_CONCEPTS, text)):
        client.log(
            Status.SUCCESS,
            f"Found a total of {len(reasons)} matching paragraphs out of "
            f"{para_count} in Terms Of Service.",
            highlight=reasons[0][1],
            paragraph=reasons[0][2],
        )
        return Status.SUCCESS

    # Words that match not-for-profit reservations.
    if len(reasons := _find_matching_paragraphs(RE_NFP_CONCEPTS, text)):
        client.log(
            Status.SUCCESS,
            f"Found total of {len(reasons)} paragraphs matching "
            f"non-commercial activities in Terms Of Service.",
            highlight=reasons[0][1],
        )
        return Status.SUCCESS

    if (size := len(text)) < 2_000:
        client.log(
            Status.FAILURE,
            f"Too little information extracted, only {size:,} bytes from "
            f"the ToS page at {url}",
        )

        # Suggest fetching page again via HTTP with Selenium.
        return Status.RETRY

    if len(RE_LEGAL_WORDS.findall(text)) < 36:
        client.log(
            Status.FAILURE,
            f"The ToS page does not appear to contain a legal text at {url}",
        )
        return Status.FAILURE

    client.log(
        Status.FAILURE,
        f"No direct matches found in {para_count} paragraphs found at {url}",
    )
    return Status.ABORT


def _extract_paragraphs(soup):
    """
    Iterator that returns a cleaned up list of paragraphs, lists items, from
    (ideally) the main body of HTML that are most likely to be legal text.
    """
    re_cleanup = re.compile("(\s+|\n|\t)")

    for para in soup.find_all(["p", "li", "ol", "ul", "span"]):
        if para.find_parent("a") or para.find_parent(["header", "footer"]):
            continue
        if para.name == "span" and para.find_parent('p'):
            continue
        if para.name in ("ol", "ul") and len(para.find_all()) > 0:
            continue

        children = [
            p for p in para.contents
            if not isinstance(p, str) or p.strip("\t\n\r ") != ""
        ]
        if len(children) == 1 and children[0].name == "a":
            continue

        text = (
            " ".join(para.findAll(text=True, recursive=True)).replace("\n", " ").strip()
        )
        if text != "":
            yield re_cleanup.sub(" ", text)
