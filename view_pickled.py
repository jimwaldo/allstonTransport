#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-03-14

@author chong

Utility to view pickled data quickly
"""
import make_name_dicts as mnd
import sys
import collections.abc as col

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python view_pickled.py [-csv] file.pkl')
        sys.exit(2)

    file = sys.argv[1]
    csv = False
    if file == "-csv":
        file = sys.argv[2]
        csv = True
    
    d = mnd.unpickle_data(file)
    if isinstance(d, col.Mapping):
        for k, v in d.items():
            if csv:
                print("%s,%s"%((str(k).strip(),str(v).strip())))
            else:
                print(k,':',v)

    elif isinstance(d, col.Iterable):
        for e in d:
            print(e)

    else:
        print ("Can't print type %s"%type(d))


    if isinstance(d, col.Sized) and not csv:
        print("Count: %s"%len(d))
