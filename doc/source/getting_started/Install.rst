======================
Setup and Installation
======================

``read-ATM1b-QFIT-binary`` is available for download from the `GitHub repository <https://github.com/tsutterley/read-ATM1b-QFIT-binary>`_,
and the `Python Package Index (pypi) <https://pypi.org/project/ATM1b-QFIT/>`_,
The contents of the repository can be download as a
`zipped file <https://github.com/tsutterley/read-ATM1b-QFIT-binary/archive/main.zip>`_  or cloned.
To use this repository, please fork into your own account and then clone onto your system.

.. code-block:: bash

    git clone https://github.com/tsutterley/read-ATM1b-QFIT-binary.git

Can then install using ``setuptools``

.. code-block:: bash

    python setup.py install

or ``pip``

.. code-block:: bash

    python3 -m pip install --user .

Alternatively can install the utilities directly from GitHub with ``pip``:

.. code-block:: bash

    python3 -m pip install --user git+https://github.com/tsutterley/read-ATM1b-QFIT-binary.git
