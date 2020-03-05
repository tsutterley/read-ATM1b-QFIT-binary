#!/usr/bin/env python
u"""
nsidc_convert_ILATM1b.py
Written by Tyler Sutterley (02/2020)

Program to read IceBridge ATM QFIT binary files datafiles directly from NSIDC
    server as bytes and output as HDF5 files
    http://nsidc.org/data/docs/daac/icebridge/ilatm1b/docs/ReadMe.qfit.txt

https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
https://nsidc.org/support/faq/what-options-are-available-bulk-downloading-data-
    https-earthdata-login-enabled
http://www.voidspace.org.uk/python/articles/authentication.shtml#base64

Register with NASA Earthdata Login system:
https://urs.earthdata.nasa.gov

Add NSIDC_DATAPOOL_OPS to NASA Earthdata Applications
https://urs.earthdata.nasa.gov/oauth/authorize?client_id=_JLuwMHxb2xX6NwYTb4dRA

CALLING SEQUENCE:
    python nsidc_convert_ILATM1b.py --user=<username> ILATM1B BLATM1B
    where <username> is your NASA Earthdata username

INPUTS:
    ILATM1B: Airborne Topographic Mapper QFIT Elevation
    BLATM1B: Pre-Icebridge Airborne Topographic Mapper QFIT Elevation
    ILNSA1B: Narrow Swath Airborne Topographic Mapper QFIT Elevation

COMMAND LINE OPTIONS:
    --help: list the command line options
    -Y X, --year=X: years to sync separated by commas
    -S X, --subdirectory=X: subdirectories to sync separated by commas
    -U X, --user=X: username for NASA Earthdata Login
    -D X, --directory: working data directory (default: current working)
    -M X, --mode=X: Local permissions mode of the directories and files synced
    -V, --verbose: Verbose output of files synced
    -C, --clobber: Overwrite existing data in transfer

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        http://www.numpy.org
    h5py: Python interface for Hierarchal Data Format 5 (HDF5)
        http://h5py.org
    lxml: Pythonic XML and HTML processing library using libxml2/libxslt
        http://lxml.de/
        https://github.com/lxml/lxml
    future: Compatibility layer between Python 2 and Python 3
        http://python-future.org/

PROGRAM DEPENDENCIES:
    count_leap_seconds.py: determines the number of leap seconds for a GPS time

UPDATE HISTORY:
    Updated 02/2020: using python3 compatible division for calculating counts
    Updated 01/2020: updated regular expression operator for extracting dates
    Updated 09/2019: added ssl context to urlopen headers
    Updated 06/2019: use strptime to extract last modified time of remote files
    Updated 12/2018: decode authorization header for python3 compatibility
    Updated 11/2018: encode base64 strings for python3 compatibility
    Updated 10/2018: updated GPS time calculation for calculating leap seconds
    Updated 07/2018 for public release
"""
from __future__ import print_function, division

import sys
import os
import re
import io
import ssl
import h5py
import getopt
import shutil
import base64
import getpass
import builtins
import posixpath
import lxml.etree
import numpy as np
import calendar, time
import read_ATM1b_QFIT_binary.count_leap_seconds
if sys.version_info[0] == 2:
    from cookielib import CookieJar
    import urllib2
else:
    from http.cookiejar import CookieJar
    import urllib.request as urllib2

#-- PURPOSE: check internet connection
def check_connection():
    #-- attempt to connect to https host for NSIDC
    try:
        HOST = 'https://n5eil01u.ecs.nsidc.org/'
        urllib2.urlopen(HOST,timeout=20,context=ssl.SSLContext())
    except urllib2.URLError:
        raise RuntimeError('Check internet connection')
    else:
        return True

#-- PURPOSE: sync the Icebridge Level-1b ATM QFIT elevation data from NSIDC
def nsidc_convert_ILATM1b(DIRECTORY, PRODUCTS, YEARS=None, SUBDIRECTORY=None,
    USER='', PASSWORD='', VERBOSE=False, CLOBBER=False, MODE=None):
    #-- Airborne Topographic Mapper Product (Level-1b)
    #-- remote directories for each dataset on NSIDC server
    remote_directories = {}
    #-- regular expression for file prefixes of each product
    remote_regex_pattern = {}
    #-- Airborne Topographic Mapper QFIT Elevation (Level-1b)
    remote_directories['ILATM1B'] = ["ICEBRIDGE","ILATM1B.001"]
    remote_directories['BLATM1B'] = ["PRE_OIB","BLATM1B.001"]
    remote_regex_pattern['ILATM1B'] = '(ILATM1B)'
    remote_regex_pattern['BLATM1B'] = '(BLATM1B)'
    #-- Narrow Swath Airborne Topographic Mapper QFIT Elevation (Level-1b)
    remote_directories['ILNSA1B'] = ["ICEBRIDGE","ILNSA1B.001"]
    remote_regex_pattern['ILNSA1B'] = '(ILNSA1B)'

    #-- https://docs.python.org/3/howto/urllib2.html#id5
    #-- create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    #-- Add the username and password for NASA Earthdata Login system
    password_mgr.add_password(None, 'https://urs.earthdata.nasa.gov',
        USER, PASSWORD)
    #-- Encode username/password for request authorization headers
    base64_string = base64.b64encode('{0}:{1}'.format(USER, PASSWORD).encode())
    #-- compile HTML parser for lxml
    parser = lxml.etree.HTMLParser()
    #-- Create cookie jar for storing cookies. This is used to store and return
    #-- the session cookie given to use by the data server (otherwise will just
    #-- keep sending us back to Earthdata Login to authenticate).
    cookie_jar = CookieJar()
    #-- create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(
        urllib2.HTTPBasicAuthHandler(password_mgr),
        urllib2.HTTPSHandler(context=ssl.SSLContext()),
        urllib2.HTTPCookieProcessor(cookie_jar))
    #-- add Authorization header to opener
    authorization_header = "Basic {0}".format(base64_string.decode())
    opener.addheaders = [("Authorization", authorization_header)]
    #-- Now all calls to urllib2.urlopen use our opener.
    urllib2.install_opener(opener)
    #-- All calls to urllib2.urlopen will now use handler
    #-- Make sure not to include the protocol in with the URL, or
    #-- HTTPPasswordMgrWithDefaultRealm will be confused.

    #-- remote https server for Icebridge Data
    HOST = 'https://n5eil01u.ecs.nsidc.org'
    #-- regular expression operator for finding icebridge-style subdirectories
    if SUBDIRECTORY:
        #-- Sync particular subdirectories for product
        R2 = re.compile('('+'|'.join(SUBDIRECTORY)+')', re.VERBOSE)
    elif YEARS:
        #-- Sync particular years for product
        regex_pattern = '|'.join('{0:d}'.format(y) for y in YEARS)
        R2 = re.compile('({0}).(\d+).(\d+)'.format(regex_pattern), re.VERBOSE)
    else:
        #-- Sync all available years for product
        R2 = re.compile('(\d+).(\d+).(\d+)', re.VERBOSE)

    #-- for each ATM product listed
    for p in PRODUCTS:
        print('PRODUCT={0}'.format(p)) if VERBOSE else None
        #-- get subdirectories from remote directory
        d=posixpath.join(HOST,remote_directories[p][0],remote_directories[p][1])
        req = urllib2.Request(url=d)
        #-- read and parse request for subdirectories (find column names)
        tree = lxml.etree.parse(urllib2.urlopen(req), parser)
        colnames = tree.xpath('//td[@class="indexcolname"]//a/@href')
        remote_sub = [sd for sd in colnames if R2.match(sd)]
        #-- for each remote subdirectory
        for sd in remote_sub:
            #-- check if data directory exists and recursively create if not
            local_dir = os.path.join(DIRECTORY,sd)
            os.makedirs(local_dir,MODE) if not os.path.exists(local_dir) else None
            #-- find Icebridge data files
            req = urllib2.Request(url=posixpath.join(d,sd))
            #-- read and parse request for remote files (columns and dates)
            tree = lxml.etree.parse(urllib2.urlopen(req), parser)
            colnames = tree.xpath('//td[@class="indexcolname"]//a/@href')
            collastmod = tree.xpath('//td[@class="indexcollastmod"]/text()')
            remote_file_lines = [i for i,f in enumerate(colnames) if
                re.match(remote_regex_pattern[p],f)]
            #-- sync each Icebridge data file
            for i in remote_file_lines:
                #-- remote and local versions of the file
                remote_file = posixpath.join(d,sd,colnames[i])
                local_file = os.path.join(local_dir,colnames[i])
                #-- get last modified date and convert into unix time
                LMD = time.strptime(collastmod[i].rstrip(),'%Y-%m-%d %H:%M')
                remote_mtime = calendar.timegm(LMD)
                #-- sync Icebridge files with NSIDC server
                http_pull_file(remote_file, remote_mtime, local_file,
                    VERBOSE, CLOBBER, MODE)
        #-- close request
        req = None

#-- PURPOSE: pull file from a remote host checking if file exists locally
#-- and if the remote file is newer than the local file
#-- read the input file and output as HDF5
def http_pull_file(remote_file,remote_mtime,local_file,VERBOSE,CLOBBER,MODE):
    #-- split extension from input ATM data file
    fileBasename, fileExtension = os.path.splitext(local_file)
    #-- copy Level-2 file from server into new HDF5 file
    if (fileExtension == '.qi'):
        local_file = '{0}.h5'.format(fileBasename)
    #-- if file exists in file system: check if remote file is newer
    TEST = False
    OVERWRITE = ' (clobber)'
    #-- check if local version of file exists
    if os.access(local_file, os.F_OK):
        #-- check last modification time of local file
        local_mtime = os.stat(local_file).st_mtime
        #-- if remote file is newer: overwrite the local file
        if (remote_mtime > local_mtime):
            TEST = True
            OVERWRITE = ' (overwrite)'
    else:
        TEST = True
        OVERWRITE = ' (new)'
    #-- if file does not exist locally, is to be overwritten, or CLOBBER is set
    if TEST or CLOBBER:
        #-- Printing files transferred
        print('{0} --> '.format(remote_file)) if VERBOSE else None
        print('\t{0}{1}\n'.format(local_file,OVERWRITE)) if VERBOSE else None
        #-- Download xml files using shutil chunked transfer encoding
        if (fileExtension == '.xml'):
            #-- Create and submit request. There are a wide range of exceptions
            #-- that can be thrown here, including HTTPError and URLError.
            request = urllib2.Request(remote_file)
            response = urllib2.urlopen(request)
            #-- chunked transfer encoding size
            CHUNK = 16 * 1024
            #-- copy contents to local file using chunked transfer encoding
            #-- transfer should work properly with ascii and binary data formats
            with open(local_file, 'wb') as f:
                shutil.copyfileobj(response, f, CHUNK)
        else:
            #-- read input data
            ATM_L1b_input,ATM_L1b_header = read_ATM_QFIT_file(remote_file)
            HDF5_icebridge_ATM1b(ATM_L1b_input, FILENAME=local_file,
                INPUT_FILE=remote_file, HEADER=ATM_L1b_header)
        #-- keep remote modification time of file and local access time
        os.utime(local_file, (os.stat(local_file).st_atime, remote_mtime))
        os.chmod(local_file, MODE)

#-- PURPOSE: read the ATM Level-1b data file
def read_ATM_QFIT_file(remote_file):
    #-- Create and submit request. There are a wide range of exceptions
    #-- that can be thrown here, including HTTPError and URLError.
    request = urllib2.Request(remote_file)
    fd = urllib2.urlopen(request)
    file_info = np.int(fd.headers["Content-Length"])
    fid = io.BytesIO(fd.read())
    #-- get the number of variables and the endianness of the file
    n_blocks,dtype = get_record_length(fid)
    MAXARG = 14
    #-- check that the number of blocks per record is less than MAXARG
    if (n_blocks > MAXARG):
        raise Exception('ERROR: Unexpected number of variables')
    #-- read over header text
    header_count,header_text = read_ATM1b_QFIT_header(fid, n_blocks, dtype)
    #-- number of records within file
    n_records = (file_info - header_count)//n_blocks//dtype.itemsize
    #-- read input data
    ATM_L1b_input = read_ATM1b_QFIT_records(fid, n_blocks, n_records, dtype)
    #-- close the input file
    fid.close()
    #-- return the data
    return ATM_L1b_input, header_text

#-- PURPOSE: get the record length and endianness of the input QFIT file
def get_record_length(fid):
    #-- assume initially big endian (all input data 32-bit integers)
    dtype = np.dtype('>i4')
    value, = np.fromstring(fid.read(dtype.itemsize), dtype=dtype, count=1)
    fid.seek(0)
    #-- swap to little endian and reread first line
    if (value > 100):
        dtype = np.dtype('<i4')
        value, = np.fromstring(fid.read(dtype.itemsize), dtype=dtype, count=1)
        fid.seek(0)
    #-- get the number of variables
    n_blocks = value//dtype.itemsize
    #-- read past first record
    np.fromstring(fid.read(n_blocks*dtype.itemsize),dtype=dtype,count=n_blocks)
    #-- return the number of variables and the endianness
    return (n_blocks, dtype)

#-- PURPOSE: get length and text of ATM1b file headers
def read_ATM1b_QFIT_header(fid, n_blocks, dtype):
    header_count = 0
    header_text = ''
    value = np.full((n_blocks), -1, dtype=np.int32)
    while (value[0] < 0):
        #-- read past first record
        line = fid.read(n_blocks*dtype.itemsize)
        value = np.fromstring(line, dtype=dtype, count=n_blocks)
        header_text += str(line[dtype.itemsize:])
        header_count += dtype.itemsize*n_blocks
    #-- rewind file to previous record and remove last record from header text
    fid.seek(header_count)
    header_text = header_text[:-dtype.itemsize*n_blocks]
    return header_count, header_text.replace('\x00','').rstrip()

#-- PURPOSE: read ATM L1b variables from a QFIT binary file
def read_ATM1b_QFIT_records(fid,n_blocks,n_records,dtype):
    #-- 10 word format = 0
    #-- 12 word format = 1
    #-- 14 word format = 2
    w = (n_blocks-10)//2
    #-- scaling factors for each variable for the 3 word formats (14 max)
    scaling_table = [
        [1e3, 1e6, 1e6, 1e3, 1, 1, 1e3, 1e3, 1e3, 1e3],
        [1e3, 1e6, 1e6, 1e3, 1, 1, 1e3, 1e3, 1e3, 1.0e1, 1, 1e3],
        [1e3, 1e6, 1e6, 1e3, 1, 1, 1e3, 1e3, 1e3, 1, 1e6, 1e6, 1e3, 1e3]]
    #-- input variable names for the 3 word formats (14 max)
    variable_table = []
    #-- 10 word format
    variable_table.append(['rel_time','latitude','longitude','elevation',
        'xmt_sigstr','rcv_sigstr','azimuth','pitch','roll','time_hhmmss'])
    #-- 12 word format
    variable_table.append(['rel_time','latitude','longitude','elevation',
        'xmt_sigstr','rcv_sigstr','azimuth','pitch','roll',
        'gps_pdop','pulse_width','time_hhmmss'])
    #-- 14 word format
    variable_table.append(['rel_time','latitude','longitude','elevation',
        'xmt_sigstr','rcv_sigstr','azimuth','pitch','roll','passive_sig',
        'pass_foot_lat','pass_foot_long','pass_foot_synth_elev','time_hhmmss'])
    #-- input variable data types for the 3 word formats (14 max)
    dtype_table = []
    #-- 10 word format
    dtype_table.append(['f','f','f','f','i','i','f','f','f','f'])
    #-- 12 word format
    dtype_table.append(['f','f','f','f','i','i','f','f','f','f','i','f'])
    #-- 14 word format
    dtype_table.append(['f','f','f','f','i','i','f','f','f','i','f','f','f','f'])
    #-- dictionary with output variables
    ATM_L1b_input = {}
    for n,d in zip(variable_table[w],dtype_table[w]):
        ATM_L1b_input[n] = np.zeros((n_records), dtype=np.dtype(d))
    #-- for each record in the ATM Level-1b file
    for r in range(n_records):
        #-- input data record r
        i = np.fromstring(fid.read(n_blocks*dtype.itemsize),
            dtype=dtype, count=n_blocks)
        #-- read variable and scale to output format
        for v,n,d,s in zip(i,variable_table[w],dtype_table[w],scaling_table[w]):
            ATM_L1b_input[n][r] = v.astype(d)/s
    #-- return the input data dictionary
    return ATM_L1b_input

#-- PURPOSE: calculate the number of leap seconds between GPS time (seconds
#-- since Jan 6, 1980 00:00:00) and UTC
def calc_GPS_to_UTC(YEAR, MONTH, DAY, HOUR, MINUTE, SECOND):
    GPS = 367.*YEAR - np.floor(7.*(YEAR + np.floor((MONTH+9.)/12.))/4.) - \
        np.floor(3.*(np.floor((YEAR + (MONTH - 9.)/7.)/100.) + 1.)/4.) + \
        np.floor(275.*MONTH/9.) + DAY + 1721028.5 - 2444244.5
    GPS_Time = GPS*86400.0 + HOUR*3600.0 + MINUTE*60.0 + SECOND
    return read_ATM1b_QFIT_binary.count_leap_seconds(GPS_Time)

#-- PURPOSE: output HDF5 file with geolocated elevation surfaces calculated
#-- from LVIS Level-1b waveform products
def HDF5_icebridge_ATM1b(ILATM1b_MDS,FILENAME=None,INPUT_FILE=None,HEADER=''):
    #-- open output HDF5 file
    fileID = h5py.File(FILENAME, 'w')

    #-- create sub-groups within HDF5 file
    fileID.create_group('instrument_parameters')

    #-- Dimensions of parameters
    n_records, = ILATM1b_MDS['elevation'].shape

    #-- regular expression pattern for extracting parameters
    rx=re.compile(('(BLATM1B|ILATM1B|ILNSA1B)_((\d{4})|(\d{2}))(\d{2})(\d{2})'
        '(.*?)\.qi$'),re.VERBOSE)
    #-- extract mission and other parameters from filename
    match_object = rx.match(os.path.basename(INPUT_FILE))
    MISSION = match_object.group(1)
    #-- convert year, month and day to int variables
    year = np.int(match_object.group(2))
    month = np.int(match_object.group(5))
    day = np.int(match_object.group(6))
    #-- early date strings omitted century and millenia (e.g. 93 for 1993)
    if match_object.group(4):
        year = (year + 1900) if (year >= 90) else (year + 2000)
    #-- extract end time from time_hhmmss variable
    hour = np.zeros((2)); minute = np.zeros((2)); second = np.zeros((2))
    for i,ind in enumerate([0,-1]):
        #-- convert to zero-padded string with 3 decimal points
        line_contents = '{0:010.3f}'.format(ILATM1b_MDS['time_hhmmss'][ind])
        hour[i] = np.float(line_contents[:2])
        minute[i] = np.float(line_contents[2:4])
        second[i] = np.float(line_contents[4:])

    #-- Defining output HDF5 variable attributes
    #-- Latitude
    attributes = {}
    attributes['latitude'] = {}
    attributes['latitude']['long_name'] = 'latitude'
    attributes['latitude']['units'] = 'degrees_north'
    attributes['latitude']['description'] = 'Laser Spot Latitude'
    #-- Longitude
    attributes['longitude'] = {}
    attributes['longitude']['long_name'] = 'Longitude'
    attributes['longitude']['units'] = 'degrees_east'
    attributes['longitude']['description'] = 'Laser Spot East Longitude'
    #-- Elevation
    attributes['elevation'] = {}
    attributes['elevation']['long_name'] = 'Elevation'
    attributes['elevation']['units'] = 'meters'
    attributes['elevation']['description'] = ('Elevation of the laser '
        'spot above ellipsoid')
    #-- Relative Time
    attributes['rel_time'] = {}
    attributes['rel_time']['long_name'] = 'Transmit time of each shot'
    attributes['rel_time']['units'] = 'seconds'
    attributes['rel_time']['description'] = ('Relative Time measured from'
        ' start of file')
    #-- time_hhmmss
    attributes['time_hhmmss'] = {}
    attributes['time_hhmmss']['long_name'] = 'Packed Time'
    attributes['time_hhmmss']['description'] = ('GPS time packed, example: '
        '153320.100 = 15 hours 33 minutes 20.1 seconds.')
    #-- azimuth
    attributes['azimuth'] = {}
    attributes['azimuth']['long_name'] = 'Scan Azimuth'
    attributes['azimuth']['units'] = 'degrees'
    attributes['azimuth']['description'] = ('Position of the rotating ATM '
        'scanner mirror.')
    attributes['azimuth']['valid_min'] = 0.0
    attributes['azimuth']['valid_max'] = 360.0
    #-- pitch
    attributes['pitch'] = {}
    attributes['pitch']['long_name'] = 'Pitch'
    attributes['pitch']['units'] = 'degrees'
    attributes['pitch']['description'] = 'Pitch component of aircraft attitude.'
    #-- roll
    attributes['roll'] = {}
    attributes['roll']['long_name'] = 'Roll'
    attributes['roll']['units'] = 'degrees'
    attributes['roll']['description'] = 'Roll component of aircraft attitude.'
    #-- gps_pdop
    attributes['gps_pdop'] = {}
    attributes['gps_pdop']['long_name'] = 'GPS Dilution of Precision'
    attributes['gps_pdop']['description'] = 'GPS Dilution of Precision (PDOP)'
    #-- pulse_width
    attributes['pulse_width'] = {}
    attributes['pulse_width']['long_name'] = 'Pulse Width'
    attributes['pulse_width']['units'] = 'counts'
    attributes['pulse_width']['description'] = ('Laser received pulse width at '
        'half height, number of digitizer samples at 0.5 nanosecond per sample.')
    #-- xmt_sigstr
    attributes['xmt_sigstr'] = {}
    attributes['xmt_sigstr']['long_name'] = 'Start Pulse Signal Strength'
    attributes['xmt_sigstr']['description'] = ('Transmitted Pulse Signal Strength'
        ' (relative).  The sum of waveform digitizer samples within the laser '
        'pulse sampled at the laser output.  Units are in digitizer counts.')
    #-- rcv_sigstr
    attributes['rcv_sigstr'] = {}
    attributes['rcv_sigstr']['long_name'] = 'Rcvd Signal Strength'
    attributes['rcv_sigstr']['description'] = ('Received Laser Signal Strength '
        '(relative).  This is the sum taken over the received pulse of the '
        'waveform samples in units of digitizer counts.')

    #-- 14 word count variables
    #-- Between 1997 and 2004 some ATM surveys included a separate sensor to
    #-- measure passive brightness. The passive data is not calibrated and
    #-- its use, if any, should  be qualitative in nature.  It may aid
    #-- the interpretation of terrain features. The measurement capability
    #-- was engineered into the ATM sensors to aid in the identification
    #-- of the water/beach interface acquired with  the instrument in
    #-- coastal mapping applications.
    attributes['passive_sig'] = {}
    attributes['passive_sig']['long_name'] = 'Passive Signal (relative)'
    attributes['passive_sig']['description'] = ("Measure of radiance reflected "
        "from the earth's surface within the vicinity of the laser pulse")
    attributes['pass_foot_lat'] = {}
    attributes['pass_foot_lat']['long_name'] = 'Passive Footprint Latitude'
    attributes['pass_foot_lat']['units'] = 'degrees'
    attributes['pass_foot_long'] = {}
    attributes['pass_foot_long']['long_name'] = 'Passive Footprint Longitude'
    attributes['pass_foot_long']['units'] = 'degrees'
    attributes['pass_foot_synth_elev'] = {}
    attributes['pass_foot_synth_elev']['long_name'] = ('Passive Footprint '
        'Synthesized Elevation')
    attributes['pass_foot_synth_elev']['units'] = 'meters'

    #-- Defining the HDF5 dataset variables
    h5 = {}
    #-- Defining data variables
    for key in ['elevation','longitude','latitude']:
        val = ILATM1b_MDS[key]
        h5[key] = fileID.create_dataset(key, (n_records,),
            data=val, dtype=val.dtype, compression='gzip')
        #-- add HDF5 variable attributes
        for att_name,att_val in attributes[key].items():
            h5[key].attrs[att_name] = att_val
    #-- instrument parameter variables
    instrument_parameters = ['rel_time','xmt_sigstr','rcv_sigstr','azimuth',
        'pitch','roll','gps_pdop','pulse_width','passive_sig','pass_foot_lat',
        'pass_foot_long','pass_foot_synth_elev','time_hhmmss']
    for key in [p for p in instrument_parameters if p in ILATM1b_MDS.keys()]:
        val = ILATM1b_MDS[key]
        h5[key] = fileID.create_dataset('instrument_parameters/{0}'.format(key),
            (n_records,), data=val, dtype=val.dtype, compression='gzip')
        #-- add HDF5 variable attributes
        for att_name,att_val in attributes[key].items():
            h5[key].attrs[att_name] = att_val

    #-- Defining global attributes for output HDF5 file
    fileID.attrs['featureType'] = 'trajectory'
    fileID.attrs['title'] = 'ATM Qfit Elevation and Return Strength'
    fileID.attrs['short_name'] = "L1B_QFIT"
    fileID.attrs['comment'] = ('Operation IceBridge products may include test '
        'flight data that are not useful for research and scientific analysis. '
        'Test flights usually occur at the beginning of campaigns. Users '
        'should read flight reports for the flights that collected any of the '
        'data they intend to use')
    fileID.attrs['summary'] = ("This data set contains spot elevation "
        "measurements of Arctic and Antarctic sea ice, and Greenland, other "
        "Arctic and Antarctic terrestrial ice surface acquired using the NASA "
        "Airborne Topographic Mapper (ATM) instrumentation. The data were "
        "collected as part of NASA Operation IceBridge funded campaigns.")
    nsidc_reference = {}
    nsidc_reference['ILATM1B'] = 'http://nsidc.org/data/ilatm1b/versions/1'
    nsidc_reference['BLATM1B'] = 'http://nsidc.org/data/BLATM1B'
    nsidc_reference['ILNSA1B'] = 'http://nsidc.org/data/ilnsa1b/versions/1'
    fileID.attrs['references'] = '{0}, {1}'.format('http://atm.wff.nasa.gov/',
        nsidc_reference[MISSION])
    fileID.attrs['date_created'] = time.strftime('%Y-%m-%d',time.localtime())
    fileID.attrs['project'] = 'NASA Operation IceBridge'
    fileID.attrs['instrument'] = 'Airborne Topographic Mapper (ATM)'
    fileID.attrs['processing_level'] = '1b'
    fileID.attrs['elevation_file'] = INPUT_FILE
    fileID.attrs['geospatial_lat_min'] = ILATM1b_MDS['latitude'].min()
    fileID.attrs['geospatial_lat_max'] = ILATM1b_MDS['latitude'].max()
    fileID.attrs['geospatial_lon_min'] = ILATM1b_MDS['longitude'].min()
    fileID.attrs['geospatial_lon_max'] = ILATM1b_MDS['longitude'].max()
    fileID.attrs['geospatial_lat_units'] = "degrees_north"
    fileID.attrs['geospatial_lon_units'] = "degrees_east"
    fileID.attrs['geospatial_ellipsoid'] = "WGS84"
    fileID.attrs['time_type'] = 'GPS'
    fileID.attrs['date_type'] = 'packed_time'
    #-- output QFIT header text
    if HEADER:
        fileID.attrs['header_text'] = HEADER
    #-- leap seconds for converting from GPS time to UTC
    S = calc_GPS_to_UTC(year,month,day,hour,minute,second)
    args = (hour[0],minute[0],second[0]-S[0])
    fileID.attrs['RangeBeginningTime']='{0:02.0f}:{1:02.0f}:{2:02.0f}'.format(*args)
    args = (hour[1],minute[1],second[1]-S[1])
    fileID.attrs['RangeEndingTime']='{0:02.0f}:{1:02.0f}:{2:02.0f}'.format(*args)
    args = (year,month,day)
    fileID.attrs['RangeBeginningDate'] = '{0:4d}:{1:02d}:{2:02d}'.format(*args)
    fileID.attrs['RangeEndingDate'] = '{0:4d}:{1:02d}:{2:02d}'.format(*args)
    time_coverage_duration = (second[1]-S[1]) - (second[0]-S[0])
    fileID.attrs['DurationTime'] ='{0:0.0f}'.format(time_coverage_duration)
    #-- Closing the HDF5 file
    fileID.close()

#-- PURPOSE: help module to describe the optional input parameters
def usage():
    print('\nHelp: {0}'.format(os.path.basename(sys.argv[0])))
    print(' -Y X, --year=X\t\tYears to sync separated by commas')
    print(' -S X, --subdirectory=X\tSubdirectories to sync separated by commas')
    print(' -U X, --user=X\t\tUsername for NASA Earthdata Login')
    print(' -D X, --directory=X\tWorking data directory')
    print(' -M X, --mode=X\t\tPermission mode of directories and files synced')
    print(' -V, --verbose\t\tVerbose output of files synced')
    print(' -C, --clobber\t\tOverwrite existing data in transfer\n')

#-- Main program that calls nsidc_convert_ILATM1b()
def main():
    #-- Read the system arguments listed after the program
    long_options = ['help','year=','subdirectory=','user=','directory=',
        'verbose','clobber','mode=']
    optlist,arglist = getopt.getopt(sys.argv[1:],'hY:S:U:D:VCM:',long_options)

    #-- command line parameters
    YEARS = None
    SUBDIRECTORY = None
    USER = ''
    DIRECTORY = os.getcwd()
    VERBOSE = False
    CLOBBER = False
    #-- permissions mode of the local directories and files (number in octal)
    MODE = 0o775
    for opt, arg in optlist:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        elif opt in ("-Y","--year"):
            YEARS = np.array(arg.split(','), dtype=np.int)
        elif opt in ("-S","--subdirectory"):
            SUBDIRECTORY = arg.split(',')
        elif opt in ("-U","--user"):
            USER = arg
        elif opt in ("-D","--directory"):
            DIRECTORY = os.path.expanduser(arg)
        elif opt in ("-V","--verbose"):
            VERBOSE = True
        elif opt in ("-C","--clobber"):
            CLOBBER = True
        elif opt in ("-M","--mode"):
            MODE = int(arg, 8)

    #-- Pre-Icebridge and IceBridge Products
    PROD = {}
    PROD['ILATM1B'] = 'Icebridge Airborne Topographic Mapper QFIT Elevation'
    PROD['BLATM1B'] = 'Pre-Icebridge Airborne Topographic Mapper QFIT Elevation'
    PROD['ILNSA1B'] = 'Narrow Swath Airborne Topographic Mapper QFIT Elevation'

    #-- enter ATM dataset to transfer as system argument
    if not arglist:
        for key,val in PROD.items():
            print('{0}: {1}'.format(key, val))
        raise Exception('No System Arguments Listed')

    #-- check that each data product entered was correctly typed
    keys = ','.join(sorted([key for key in PROD.keys()]))
    for p in arglist:
        if p not in PROD.keys():
            raise IOError('Incorrect Data Product Entered ({0})'.format(keys))

    #-- NASA Earthdata hostname
    HOST = 'urs.earthdata.nasa.gov'
    #-- check that NASA Earthdata credentials were entered
    if not USER:
        USER = builtins.input('Username for {0}: '.format(HOST))
    #-- enter password securely from command-line
    PASSWORD = getpass.getpass('Password for {0}@{1}: '.format(USER,HOST))

    #-- check internet connection before attempting to run program
    if check_connection():
        nsidc_convert_ILATM1b(DIRECTORY, arglist, USER=USER, PASSWORD=PASSWORD,
            YEARS=YEARS, SUBDIRECTORY=SUBDIRECTORY, VERBOSE=VERBOSE,
            CLOBBER=CLOBBER, MODE=MODE)

#-- run main program
if __name__ == '__main__':
    main()
