read-ATM1b-QFIT-binary
======================

#### Reads Level-1b Airborne Topographic Mapper (ATM) QFIT binary data products  

- [IceBridge ATM L1B Qfit Elevation and Return Strength](https://nsidc.org/data/ilatm1b/1)  
- [IceBridge Narrow Swath ATM L1B Qfit Elevation and Return Strength](https://nsidc.org/data/ilnsa1b/1)  
- [NSIDC IceBridge Software Tools](https://nsidc.org/data/icebridge/tools.html)
- [Python program for retrieving Operation IceBridge data](https://github.com/tsutterley/nsidc-earthdata)

#### Calling Sequence
```
from read_ATM1b_QFIT_binary import read_ATM1b_QFIT_binary
ATM_L1b_input, ATM_L1b_header = read_ATM1b_QFIT_binary('example_filename.qi')
```

#### `nsidc_convert_ILATM1b.py`
Alternative program to read IceBridge ATM QFIT binary files files directly from NSIDC server as bytes and output as HDF5 files  

#### Dependencies
- [numpy: Scientific Computing Tools For Python](http://www.numpy.org)
- [h5py: Python interface for Hierarchal Data Format 5 (HDF5)](http://h5py.org)  
- [lxml: processing XML and HTML in Python](https://pypi.python.org/pypi/lxml)
- [future: Compatibility layer between Python 2 and Python 3](http://python-future.org/)  

#### Download
The program homepage is:   
https://github.com/tsutterley/read-ATM1b-QFIT-binary    
A zip archive of the latest version is available directly at:    
https://github.com/tsutterley/read-ATM1b-QFIT-binary/archive/master.zip  

#### Disclaimer  
This program is not sponsored or maintained by the Universities Space Research Association (USRA), the National Snow and Ice Data Center (NSIDC) or NASA.  It is provided here for your convenience but _with no guarantees whatsoever_.  

[Program inspired by the QFIT C reader provided on NSIDC](ftp://sidads.colorado.edu/pub/tools/icebridge/qfit/c/)   
