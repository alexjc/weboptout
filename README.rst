Web Opt-Out
===========

A tool and library written in Python to check the Copyright information of online works and the conditions under which they can be accessed.  See the `examples` folder to get started.

The source code is available in this repository and there are packaged releases available from PyPI that include verified databases. Requires Python 3.9+!

Usage
-----

The library supports checking if files hosted on a domain or CDN are opted-out of Text- and Data-Mining:

.. code-block:: python

    from weboptout import check_domain_reservation, rsv

    res = check_domain_reservation("pinterest.com")
    if res == rsv.YES:
        print(f"Domain Opted-Out\n\t{res.url}\n\t❝{res.summary}〞")


You may call the API functions like `check_domain_reservation` in both synchronous and asynchronous forms.


Installation
------------

Option 1) Install from PyPI [recommended]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install weboptout


Option 2) Setup From Source [developers]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install poetry
    poetry install


Terms & Conditions
------------------

This project has dual licensing, both of which you must respect if you use packaged releases:

* **The source code in this repository is covered by the MIT license.**
* **The database in packaged releases is under a Fair Dealings Licence.**

Please note that this project does not provide WARRANTY, and attempts to claim WARRANTY for NON-INFRINGEMENT in the context of regulatory or contractual compliance will be considered a punishable breach of the LICENSE terms.  DAMAGES are set at €250,000.
