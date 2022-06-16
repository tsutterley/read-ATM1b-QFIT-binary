#!/usr/bin/env python
u"""
time.py
Written by Tyler Sutterley (05/2022)
Utilities for calculating time operations

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        https://numpy.org
    dateutil: powerful extensions to datetime
        https://dateutil.readthedocs.io/en/stable/
    lxml: processing XML and HTML in Python
        https://pypi.python.org/pypi/lxml

PROGRAM DEPENDENCIES:
    utilities.py: download and management utilities for syncing files

UPDATE HISTORY:
    Updated 05/2022: changed keyword arguments to camel case
    Updated 04/2022: updated docstrings to numpy documentation format
    Updated 04/2021: updated NIST ftp server url for leap-seconds.list
    Updated 03/2021: replaced numpy bool/int to prevent deprecation warnings
    Updated 02/2021: NASA CDDIS anonymous ftp access discontinued
    Updated 01/2021: added ftp connection checks
        add date parser for cases when only a calendar date with no units
    Updated 12/2020: merged with convert_julian and convert_calendar_decimal
        added calendar_days routine to get number of days per month
    Updated 09/2020: added wrapper function for merging Bulletin-A files
        can parse date strings in form "time-units since yyyy-mm-dd hh:mm:ss"
    Updated 08/2020: added NASA Earthdata routines for downloading from CDDIS
    Written 07/2020
"""
import re
import datetime
import numpy as np
import ATM1b_QFIT.utilities

#-- PURPOSE: convert times from seconds since epoch1 to time since epoch2
def convert_delta_time(delta_time, epoch1=None, epoch2=None, scale=1.0):
    """
    Convert delta time from seconds since ``epoch1`` to time since ``epoch2``

    Parameters
    ----------
    delta_time: float
        seconds since epoch1
    epoch1: tuple or NoneType, default None
        epoch for input delta_time
    epoch2: tuple or NoneType, default None
        epoch for output delta_time
    scale: float, default 1.0
        scaling factor for converting time to output units
    """
    epoch1 = datetime.datetime(*epoch1)
    epoch2 = datetime.datetime(*epoch2)
    delta_time_epochs = (epoch2 - epoch1).total_seconds()
    #-- subtract difference in time and rescale to output units
    return scale*(delta_time - delta_time_epochs)

#-- PURPOSE: calculate the delta time from calendar date
#-- http://scienceworld.wolfram.com/astronomy/JulianDate.html
def convert_calendar_dates(year, month, day, hour=0.0, minute=0.0, second=0.0,
    epoch=(1992,1,1,0,0,0), scale=1.0):
    """
    Calculate the time in time units since ``epoch`` from calendar dates

    Parameters
    ----------
    year: float
        calendar year
    month: float
        month of the year
    day: float
        day of the month
    hour: float, default 0.0
        hour of the day
    minute: float, default 0.0
        minute of the hour
    second: float, default 0.0
        second of the minute
    epoch: tuple, default (1992,1,1,0,0,0)
        epoch for output delta_time
    scale: float, default 1.0
        scaling factor for converting time to output units

    Returns
    -------
    delta_time: float
        days since epoch
    """
    #-- calculate date in Modified Julian Days (MJD) from calendar date
    #-- MJD: days since November 17, 1858 (1858-11-17T00:00:00)
    MJD = 367.0*year - np.floor(7.0*(year + np.floor((month+9.0)/12.0))/4.0) - \
        np.floor(3.0*(np.floor((year + (month - 9.0)/7.0)/100.0) + 1.0)/4.0) + \
        np.floor(275.0*month/9.0) + day + hour/24.0 + minute/1440.0 + \
        second/86400.0 + 1721028.5 - 2400000.5
    epoch1 = datetime.datetime(1858,11,17,0,0,0)
    epoch2 = datetime.datetime(*epoch)
    delta_time_epochs = (epoch2 - epoch1).total_seconds()
    #-- return the date in days since epoch
    return scale*np.array(MJD - delta_time_epochs/86400.0,dtype=np.float64)

#-- PURPOSE: Count number of leap seconds that have passed for each GPS time
def count_leap_seconds(GPS_Time, truncate=True):
    """
    Counts the number of leap seconds between a given GPS time and UTC

    Parameters
    ----------
    GPS_Time: float
        seconds since January 6, 1980 at 00:00:00
    truncate: bool, default True
        Reduce list of leap seconds to positive GPS times

    Returns
    -------
    n_leaps: float
        number of elapsed leap seconds
    """
    #-- get the valid leap seconds
    leaps = get_leap_seconds(truncate=truncate)
    #-- number of leap seconds prior to GPS_Time
    n_leaps = np.zeros_like(GPS_Time,dtype=np.float64)
    for i,leap in enumerate(leaps):
        count = np.count_nonzero(GPS_Time >= leap)
        if (count > 0):
            indices = np.nonzero(GPS_Time >= leap)
            n_leaps[indices] += 1.0
    #-- return the number of leap seconds for converting to UTC
    return n_leaps

#-- PURPOSE: Define GPS leap seconds
def get_leap_seconds(truncate=True):
    """
    Gets a list of GPS times for when leap seconds occurred

    Parameters
    ----------
    truncate: bool, default True
        Reduce list of leap seconds to positive GPS times

    Returns
    -------
    GPS time: float
        GPS seconds when leap seconds occurred
    """
    leap_secs = ATM1b_QFIT.utilities.get_data_path(['data','leap-seconds.list'])
    #-- find line with file expiration as delta time
    with open(leap_secs,'r') as fid:
        secs, = [re.findall(r'\d+',i).pop() for i in fid.read().splitlines()
            if re.match(r'^(?=#@)',i)]
    #-- check that leap seconds file is still valid
    expiry = datetime.datetime(1900,1,1) + datetime.timedelta(seconds=int(secs))
    today = datetime.datetime.now()
    update_leap_seconds() if (expiry < today) else None
    #-- get leap seconds
    leap_UTC,TAI_UTC = np.loadtxt(ATM1b_QFIT.utilities.get_data_path(leap_secs)).T
    #-- TAI time is ahead of GPS by 19 seconds
    TAI_GPS = 19.0
    #-- convert leap second epochs from NTP to GPS
    #-- convert from time of 2nd leap second to time of 1st leap second
    leap_GPS = convert_delta_time(leap_UTC+TAI_UTC-TAI_GPS-1,
        epoch1=(1900,1,1,0,0,0), epoch2=(1980,1,6,0,0,0))
    #-- return the GPS times of leap second occurance
    if truncate:
        return leap_GPS[leap_GPS >= 0].astype(np.float64)
    else:
        return leap_GPS.astype(np.float64)

#-- PURPOSE: connects to servers and downloads leap second files
def update_leap_seconds(timeout=20, verbose=False, mode=0o775):
    """
    Connects to servers to download leap-seconds.list files from NIST servers

    - https://www.nist.gov/pml/time-and-frequency-division/leap-seconds-faqs

    Servers and Mirrors

    - ftp://ftp.nist.gov/pub/time/leap-seconds.list
    - https://www.ietf.org/timezones/data/leap-seconds.list

    Parameters
    ----------
    timeout: int, default 20
        timeout in seconds for blocking operations
    verbose: bool, default False
        print file information about output file
    mode: oct, default 0o775
        permissions mode of output file
    """
    #-- local version of file
    FILE = 'leap-seconds.list'
    LOCAL = ATM1b_QFIT.utilities.get_data_path(['data',FILE])
    HASH = ATM1b_QFIT.utilities.get_hash(LOCAL)

    #-- try downloading from NIST ftp servers
    HOST = ['ftp.nist.gov','pub','time',FILE]
    try:
        ATM1b_QFIT.utilities.check_ftp_connection(HOST[0])
        ATM1b_QFIT.utilities.from_ftp(HOST, timeout=timeout, local=LOCAL,
            hash=HASH, verbose=verbose, mode=mode)
    except:
        pass
    else:
        return

    #-- try downloading from Internet Engineering Task Force (IETF) mirror
    REMOTE = ['https://www.ietf.org','timezones','data',FILE]
    try:
        ATM1b_QFIT.utilities.from_http(REMOTE, timeout=timeout, local=LOCAL,
            hash=HASH, verbose=verbose, mode=mode)
    except:
        pass
    else:
        return
