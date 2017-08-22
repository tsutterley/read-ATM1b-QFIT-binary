read-ATM1b-QFIT-binary
================

#### Reads Level-1b Airborne Topographic Mapper (ATM) QFIT binary data products  

- [IceBridge ATM L1B Qfit Elevation and Return Strength](https://nsidc.org/data/docs/daac/icebridge/ilatm1b/v1/index.html)  
- [IceBridge Narrow Swath ATM L1B Qfit Elevation and Return Strength](https://nsidc.org/data/docs/daac/icebridge/ilnsa1b/v1/index.html)  
- [NSIDC IceBridge Software Tools](http://nsidc.org/data/icebridge/tools.html)

#### Calling Sequence
```
from read_ATM1b_QFIT_binary import read_ATM1b_QFIT_binary
ATM_L1b_input, ATM_L1b_header = read_ATM1b_QFIT_binary('example_filename.qi')
```

#### Dependencies
[numpy: Scientific Computing Tools For Python](http://www.numpy.org)

#### Download
The program homepage is:   
https://github.com/tsutterley/read-ATM1b-QFIT-binary    
A zip archive of the latest version is available directly at:    
https://github.com/tsutterley/read-ATM1b-QFIT-binary/archive/master.zip  

#### Disclaimer  
This program is not sponsored or maintained by the Universities Space Research Association (USRA), the National Snow and Ice Data Center (NSIDC) or NASA.  It is provided here for your convenience but _with no guarantees whatsoever_.  

[Program inspired by the QFIT C reader provided on NSIDC](ftp://sidads.colorado.edu/pub/tools/icebridge/qfit/c/)   
