Installation
============

Prerequisites
-------------

Before installing Parseltongue, ensure you have the following:

* Python 3.6 or higher
* GemStone/S 64 installed (version 3.4.0 to 3.7.x supported)
* Environment variable ``GEMSTONE`` set to your GemStone installation directory
* Environment ``LD_LIBRARY_PATH`` set to ``$GEMSTONE/lib``


Installing from PyPI
--------------------

.. code-block:: bash

    pip install parseltongue

Installing from Source
----------------------

Clone the repository and install in development mode (with test dependencies):

.. code-block:: bash

    git clone https://github.com/reahl/parseltongue.git
    cd parseltongue
    pip install -e .[test]

Building Documentation
----------------------

To build the documentation:

.. code-block:: bash

    # Install the documentation dependencies
    pip install -e ".[docs]"

    # Generate the documentation
    cd docs
    make html

The documentation will be available in the ``docs/_build/html`` directory.
