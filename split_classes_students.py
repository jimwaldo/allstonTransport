#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 10:18:18 2018

@author: waldo

Taking the overall enrollment file (as a csv) provided by the registrar, builds and saves three sets that get used
by later programs. One of these is the classes that will be taught in Allston; this is determined by seeing if the subject
is in the set read in from the second command-line argument, seas_subject_set_file.pkl. Also built is the set of
students who took one of these classes. The third set is the set of all classes taken by the students who take at least
one class that will be in Allston. These three sets are saved as pickles in the directory in which the program is run.
"""
import csv, sys, pickle
import make_name_dicts as mnd

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python split_classes_students.py enrollment_file.csv seas_subject_set_file.pkl')
        sys.exit(1)

    fname = sys.argv[1]
    fin = open(fname, 'r')
    cin = csv.reader(fin)
    f_p = open(sys.argv[2], 'rb')
    seas_subject_s = pickle.load(f_p)
    f_p.close()
    #TODO: Currently the determination of what classes are in Allston is done on a subject basis. This
    #    should be changed to allow a set of classes to be passed in to allow fine-grained control

    h = next(cin)
    student_s = set()
    allston_class_s = set()
    allston_student_class_s = set()

    for l in cin:
        if l[3] in seas_subject_s:
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
