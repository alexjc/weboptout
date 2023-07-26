## Copyright © 2023, Alex J. Champandard.  Licensed under MIT; see LICENSE! ⚘

import enum


class Status(enum.Enum):
    """
    Enumeration of status codes that can be used as return values to indicate
    the result of an operation, or as the status code of a log record.
    """

    SUCCESS = 1
    FAILURE = 0
    RETRY = -1
    ABORT = -2


class Reservation:
    """
    A reservation of rights and all the information that goes with it, in
    order to provide explanations.  The reservation can apply to any concept,
    including a domain, a URL, a file.

    This class is intended to be used via the `rsv` namespace, along with the
    defaults YES, MAYBE, NO.  These can be cloned via the __call__ function to
    create Reservations derived from that default.
    """

    def __init__(self, id: int, summary: str = None, url: str = None, records: list = None):
        self._id = id
        self.summary = summary
        self.url = url
        self.records = records or []

    def __eq__(self, id: int):
        return self._id == id

    def __repr__(self):
        return f'<weboptout.Reservation id={self._id} url="{self.url}" summary="{self.summary}">'

    def __call__(self, /, summary: str, url: str = None, records: list = None):
        return Reservation(self._id, summary, url, records)


class rsv:
    """
    Namespace with default Reservations that can be cloned and used for comparison.
    """

    YES = Reservation(2)
    MAYBE = Reservation(1)
    NO = Reservation(0)
    ERROR = Reservation(-1)
