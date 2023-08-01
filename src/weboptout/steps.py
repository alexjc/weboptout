## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

from enum import Enum


class Steps(Enum):
    # HTTP
    ResolveDomain = "resolving domain"
    EstablishConnection = "establishing connection"
    RetrieveContent = "retrieving content"
    CheckErrorCode = "checking HTTP response code"
    ValidateContentLength = "validate the length of the content"
    ValidateContentFormat = "validate the format of the content"
    ValidateContentEncoding = "validate encoding of content"
    ValidateContentLanguage = "validating the language of the content"

    # HTML
    RetrievePage = "retrieving the page via HTTP"
    ParsePage = "parsing page as HTML"
    ValidatePageLanguage = "validating the language of HTML page"
    ValidatePageLinks = "validating the links within the HTML page"
    FindPageLinks = "finding the links within the HTML page"
    FindSomeLinksToTerms = "finding links to ToS pages"
    FindGoodLinksToTerms = "finding good links to ToS pages"
    ParsePageContent = "parsing page content"

    # TEXT
    ExtractText = "extracting text from page"
    ValidateTextLength = "validating text length"
    ValidateTextLanguage = "validating language from ToS text"
    ValidateLegalText = "validating text by checking legal words"
    ExtractParagraphs = "extracting paragraphs from text"
    ValidateParagraphs = "validating paragraphs extracted"

    # LEGAL
    ExtractLegalParagraphs = "extracting legal paragraphs"
    MatchTermsInclusion = "matching terms that include paragraphs"
    FilterTermsExclusion = "matching terms that exclude paragraphs"
    MatchFoundBest = "matching best paragraph"
