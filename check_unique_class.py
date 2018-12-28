#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 26 13:02:19 2018

@author: waldo
"""
import csv, sys

def check_class_unique(csv_in):
    class_set = set()
    class_course_set = set()
    for l in csv_in:
        class_set.add(l[1])
        class_course_set.add(l[1]+l[2])
        
    return class_set, class_course_set

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: check_unique filename ...")
        exit(1)
            
    for a in range(1, len(sys.argv)):
        fin = open(sys.argv[a], 'r')
        cin = csv.reader(fin)
        h = next(cin)
        
        set_1, set_2 = check_class_unique(cin)
        print(sys.argv[a],len(set_1), len(set_2))
        fin.close()
