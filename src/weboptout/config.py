## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import re


# Expected href content of links to Terms Of Service.
RE_HREF_TOS = re.compile("""\
(terms|agreement|polic(y|ies)|user|legal|/tou/?$|/tos/?$)\
""", re.I)

# Expected text content for links to Terms Of Service.
RE_TEXT_TOS = re.compile("""(\
^terms of service|^terms of use|^terms (&|and) condition|^Terms$|^Legal$|\
use polic(y|ies)$|^user agreement$|^TOU$|^TOS$|terms(.+)(service|condition)|\
terms|legal|conditions|guidelines\
)""", re.I)

# Parts of words that indicate a TDM activity, ordered by confidence.
RE_TDM_CONCEPTS = [
    re.compile(p, re.I) for p in [
        "(scrap(e|er|ing)|data[\s-]min(e|ing))",
        "(spider|robot|crawl(ing|er)?|index(ing|er))",
        "automated (software|tool|mean|system|way|device)s?",
        "(image library|machine learning|deep leaning|populate a database)",
        "(extract|compil(e|at)?|collect)(ing|ion)? (data|content|material|information)",
        "harvest(ing|er)?",
    ]
]

# Bag-of-words that represent legal concepts to detect legal documents.
RE_LEGAL_WORDS = re.compile("""\
(effective|accept|entitle|dispute|providing|unable|reasonable|applicable|\
precludes|enforcement|reserve|terminate|section|constitute|damages|liable|\
obligations|information|processing|consent|privacy|limited|necessary|\
purpose|decide|account|security|request|protection\
)""", re.I)
