#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 10:18:18 2018

@author: waldo

Taking the overall enrollment file (as a csv) provided by the registrar, builds and saves three sets that get used
by later programs. One of these is the classes that will be taught in Allston; this is determined by using the function will_be_allston_course in the file allston_course_selector.py. Also built is the set of
students who took one of these classes. The third set is the set of all classes taken by the students who take at least
one class that will be in Allston. These three sets are saved as pickles in the directory in which the program is run.
"""
import csv, sys, pickle
import make_name_dicts as mnd
import allston_course_selector as acs

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python split_classes_students.py enrollment_file.csv')
        sys.exit(1)

    fname = sys.argv[1]
    fin = open(fname, 'r')
    cin = csv.reader(fin)

    h = next(cin)
    student_s = set()
    allston_class_s = set()
    allston_student_class_s = set()

    for l in cin:
        if acs.will_be_allston_course(l):
            allston_class_s.add(l[1])
            student_s.add(l[8])

    fin.seek(0)
    h = next(cin)
    for l in cin:
        if l[8] in student_s:
            allston_student_class_s.add(l[1])
    fin.close()

    mnd.pickle_data('Allston_class_set.pkl', allston_class_s)
    mnd.pickle_data('Allston_student_set.pkl', student_s)
    mnd.pickle_data('all_allston_student_classes_set.pkl', allston_student_class_s)
