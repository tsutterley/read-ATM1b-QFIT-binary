#!/usr/bin/env python
u"""
count_leap_seconds.py (06/2022)
Count number of leap seconds that have passed for each GPS time
"""
import warnings
import ATM1b_QFIT.time

def count_leap_seconds(*args,**kwargs):
    warnings.filterwarnings("always")
    warnings.warn("Deprecated. Please use time module instead",DeprecationWarning)
    # call renamed version to not break workflows
    return ATM1b_QFIT.time.count_leap_seconds(*args)
