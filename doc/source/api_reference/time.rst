=======
time.py
=======

Utilities for calculating time operations

 - Can calculate the time in days since epoch from calendar dates
 - Can count the number of leap seconds between a given GPS time and UTC
 - Syncs leap second files with NIST servers

Calling Sequence
----------------

Count the number of leap seconds between a GPS time and UTC

.. code-block:: python

    import ATM1b_QFIT.time
    leap_seconds = ATM1b_QFIT.time.count_leap_seconds(gps_seconds)

Convert a calendar date into Modified Julian Days

.. code-block:: python

    import ATM1b_QFIT.time
    MJD = ATM1b_QFIT.time.convert_calendar_dates(YEAR,MONTH,DAY,hour=HOUR,
        minute=MINUTE,second=SECOND,epoch=(1858,11,17,0,0,0))

`Source code`__

.. __: https://github.com/tsutterley/read-ATM1b-QFIT-binary/blob/main/read_ATM1b_QFIT_binary/time.py


General Methods
===============

.. autofunction:: ATM1b_QFIT.time.convert_delta_time

.. autofunction:: ATM1b_QFIT.time.convert_calendar_dates

.. autofunction:: ATM1b_QFIT.time.count_leap_seconds

.. autofunction:: ATM1b_QFIT.time.get_leap_seconds

.. autofunction:: ATM1b_QFIT.time.update_leap_seconds
