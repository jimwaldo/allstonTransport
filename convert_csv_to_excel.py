#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Monday July 13

@author: chong
"""

import sys

from pathlib import Path


from pandas.io.excel import ExcelWriter
import pandas




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python convert_csv_to_excel.py file1.csv ...')
        sys.exit(1)

    for infile in sys.argv[1:]:
        outfile = Path(infile).stem + ".xlsx"
        print("Processing %s to %s"%(infile, outfile));

        with ExcelWriter(outfile) as ew:
            pandas.read_csv(infile).to_excel(ew, index=False, sheet_name='Course Conflicts')

