#!/usr/bin/env python
# Parses a TotalPhase protocol analyzer's EXPORT CSV file.

import usb2
import re

########################
###       MAIN       ###
########################

my_pa = usb2.ProtocolAnalyzer( name = 'Kepler PNF3010', ds_type = 'csv', ds_name = 'enumeration.csv' )
my_pa.start()
my_pa.displayPktsFormatted()
