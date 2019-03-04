#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 2018

@author: waldo

Build a dictionary keyed by class number with values course time objects, which contain the class number, the start
and end time, an indicator of where the class is taught (Cambridge or Allston), and a list indicating the days of the
week that the course meets. The courses for which the dictionary is built is determined by the set of classes handed
in as the second command-line argument; the third command-line argument is the set of classes that are taught in
Allston. If a class is not in this set, it is assumed to be taught in Cambridge. The first command-line argument is
a csv file provided by the registrar containing all of the course time information.
"""
import csv, sys
import make_name_dicts as mnd
import class_time as ct

def build_ct_d(csv_in, c_filter, allston_c_s):
    """
    Build a dictionary indexed by course_num with values course_time objects that will indicate the start time,
    end time, and days of the week for each course, along with where the course is taught.
    :param csv_in: A csv file in the format of the course_time.csv supplied by the registrat
    :param c_filter: the set of classes that will be in the dictionary; should be all of the classes taken by any
    student who takes a class located in Allston
    :param allston_c_s: The set of classes being taught in Allston
    :return: a dictionary indexed by course_num with values course_time objects
    """
    ret_d = {}
    for l in csv_in:
        if l[1] in c_filter:
            ret_d[l[1]] = ct.course_time(l, l[1] in allston_c_s)
    return ret_d

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python build_course_time.py course_times.csv class_set_filter.pkl allston_class_set.pkl')
        sys.exit(1)

    fin = sys.argv[2]
    class_filter_s = mnd.unpickle_data(fin)

    fin = sys.argv[3]
    allston_class_s = mnd.unpickle_data(fin)

    fin = open(sys.argv[1])
    cin = csv.reader(fin)
    h = next(cin)

    class_time_d = build_ct_d(cin, class_filter_s, allston_class_s)

    fin.close()
    mnd.pickle_data('class_time_d.pkl', class_time_d)