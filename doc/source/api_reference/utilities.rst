============
utilities.py
============

Download and management utilities for syncing time and auxiliary files

 - Can list a directory on a ftp host
 - Can download a file from a ftp or http host
 - Can download a file from CDDIS via https when NASA Earthdata credentials are supplied
 - Checks ``MD5`` or ``sha1`` hashes between local and remote files

`Source code`__

.. __: https://github.com/tsutterley/read-ATM1b-QFIT-binary/blob/main/ATM1b_QFIT/utilities.py


General Methods
===============

.. autofunction:: ATM1b_QFIT.utilities.get_data_path

.. autofunction:: ATM1b_QFIT.utilities.file_opener

.. autofunction:: ATM1b_QFIT.utilities.get_hash

.. autofunction:: ATM1b_QFIT.utilities.url_split

.. autofunction:: ATM1b_QFIT.utilities.get_unix_time

.. autofunction:: ATM1b_QFIT.utilities.even

.. autofunction:: ATM1b_QFIT.utilities.ceil

.. autofunction:: ATM1b_QFIT.utilities.copy

.. autofunction:: ATM1b_QFIT.utilities.check_ftp_connection

.. autofunction:: ATM1b_QFIT.utilities.ftp_list

.. autofunction:: ATM1b_QFIT.utilities.from_ftp

.. autofunction:: ATM1b_QFIT.utilities.http_list

.. autofunction:: ATM1b_QFIT.utilities.from_http

.. autofunction:: ATM1b_QFIT.utilities.attempt_login

.. autofunction:: ATM1b_QFIT.utilities.build_opener

.. autofunction:: ATM1b_QFIT.utilities.check_credentials

.. autofunction:: ATM1b_QFIT.utilities.cddis_list

.. autofunction:: ATM1b_QFIT.utilities.from_cddis
