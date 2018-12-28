#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 26 12:40:03 2018

@author: waldo

Splits a file, handed in as a csv.reader, into files that are separated by
the term. Assumes that the term is in the form shown in the term_s and term_l
structures. Creates a file per term, with the same content layout as the incoming
file. 
"""

import csv

def split_file_by_term(from_file, out_name_base):
    
    term_s = {'2015 Fall','2016 Fall','2016 Spring','2017 Fall','2017 Spring',
              '2018 Fall','2018 Spring'}
    term_l = ['2015 Fall','2016 Fall','2016 Spring','2017 Fall','2017 Spring',
              '2018 Fall','2018 Spring']
    term_names_l = ['2015_Fall', '2016_Fall', '2016_Spring', '2017_Fall', 
                    '2017_Spring','2018_Fall','2018_Spring']
    
    csv_d = {}
    i = 0
    for t in term_l:
        print(t)
        csv_d[t] = csv.writer(open(term_names_l[i] + out_name_base + '.csv', 'w'))
        i += 1
        
    h = next(from_file)
    min_len = len(h)
    
    for v in csv_d.values():
        v.writerow(h)
        
    for l in from_file:
        if len(l) < min_len:
            continue
        if l[0] in term_s:
            csv_d[l[0]].writerow(l)
            
    return


