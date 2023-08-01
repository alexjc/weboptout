## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import re
import warnings
import langdetect
from bs4 import BeautifulSoup

from .types import Status
from .config import RE_TDM_CONCEPTS, RE_LEGAL_WORDS, RE_NFP_CONCEPTS
from .steps import Steps as S


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
    with warnings.catch_warnings(record=True) as w:
        soup = BeautifulSoup(html, "html.parser")

    with client.setup_log() as report:
        report(S.ParsePage, fail=len(w) > 0, url=url, **{'html': html, 'warnings': w} if len(w) > 0 else {})

        text = "\n".join(_extract_paragraphs(soup))

        report(S.ExtractText, fail=len(text) < 500, bytes=len(text), paragraphs=text.count("\n")+1)

        # Only English language is currently supported.
        lang = langdetect.detect(text)
        report(S.ValidateTextLanguage, fail=bool(lang != "en"), lang=lang)
        assert lang == 'en'

        # Words that match data-mining concepts.
        reasons = _find_matching_paragraphs(RE_TDM_CONCEPTS, text)
        if len(reasons) > 0:
            client._output.append((1234, reasons[0][1], reasons[0][2]))

        report(
            S.ExtractParagraphs,
            succeed=len(reasons) > 0,
            type="Text- and Data-Mining",
            paragraphs=len(reasons),
        )

        # Words that match not-for-profit reservations.
        reasons = _find_matching_paragraphs(RE_NFP_CONCEPTS, text)
        if len(reasons) > 0:
            client._output.append((5678, reasons[0][1], reasons[0][2]))

        report(
            S.ExtractParagraphs,
            succeed=len(reasons) > 0,
            type="Not-For-Profit",
            paragraphs=len(reasons),
        )

        report(S.ExtractText, fail=len(text) < 2_000)

        legal_words = RE_LEGAL_WORDS.findall(text)
        report(S.ValidateLegalText, fail=len(legal_words) < 36)

    if tuple(client._steps[-1][0:2]) == (Status.FAILURE, S.ValidateTextLanguage):
        return Status.ABORT

    if tuple(client._steps[-1][0:2]) == (Status.FAILURE, S.ExtractText):
        return Status.RETRY

    assert len(client._steps) > 0
    assert report.status is not None
    return report.status


def _extract_paragraphs(soup):
    """
    Iterator that returns a cleaned up list of paragraphs, lists items, from
    (ideally) the main body of HTML that are most likely to be legal text.
    """
    re_cleanup = re.compile("(\s+|\n|\t)")

    for para in soup.find_all(["p", "li", "ol", "ul", "span"]):
        if para.find_parent("a") or para.find_parent(["header", "footer"]):
            continue
        if para.name == "span" and para.find_parent("p"):
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
