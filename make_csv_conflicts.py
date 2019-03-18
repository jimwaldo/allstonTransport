#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-03-05

@author waldo

Uses a list of dictionaries of times and transitions, created by build_transition_time_d.py, and creates a
csv file with the times and transition. Allows importing into a spreadsheet and easy viewing. An alternative to the
graphical display in display_trans_times.py
"""
import pickle, csv, sys

import display_trans as dt
import make_name_dicts as md
import operator as op

def write_conflicts_csv(conflicts_d, c_in, csv_out):
    """
    From a list (one per day) of dictionaries indexed by time with entries the list of number of students to Allston and
    number of students to Cambridge, write a csv file that contains the table of times and transitions.
    :param conflicts_d: A dictionary from conflct pairs to counts of conflicts
    :param c_in: an open CSV file containing the course time info (i.e., course_times.csv)
    :param csv_out: an open and writeable csv file to which the data is to be written
    :return: None
    """

    # We will be nice and get the set of all courses, and sort by subject.
    courses = set()
    courses.update([x[0] for x in conflicts_d.keys()])
    courses.update([x[1] for x in conflicts_d.keys()])

    if c_in != None:
        # build up some more readable course names
        courses_d = {}
        for l in c_in:
            (class_num, subject, catalog, component) = (l[1], l[3], l[4], l[7])
            if class_num in courses:
                courses_d[class_num] = (subject, catalog, component)

        # Now we go through and print everything
        header_l =[ 'Course1 Subject', 'Course1 Catalog', 'Course1 Component', 'Course1 ClassNum', 'Course2 Subject', 'Course2 Catalog', 'Course2 Component', 'Course2 ClassNum', 'Course1<Course2','Num students']
        csv_out.writerow(header_l)

        for (c1, c2), count in conflicts_d.items():
            info1 = courses_d[c1]
            info2 = courses_d[c2]
            csv_out.writerow([info1[0], info1[1], info1[2], c1, info2[0], info2[1], info2[2], c2, "TRUE", count])
            csv_out.writerow([info2[0], info2[1], info2[2], c2, info1[0], info1[1], info1[2], c1, "FALSE", count])
        
        return


    header_l =[ 'Course1 ClassNum', 'Course2 ClassNum','Num students']        
    csv_out.writerow(header_l)

    # Go through each
    for (c1, c2), count in conflicts_d.items():
        csv_out.writerow([c1, c2, count])

if __name__ == '__main__':
    def usage():
        print('Usage: python make_csv_conflicts.py [course_times.csv] out_file.csv')
        sys.exit(1)

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()

    c_in = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "course_times.csv":
            # likely entered by accident
            usage()
            
        out_file = open(sys.argv[1], 'w')
    else:
        out_file = open(sys.argv[2], 'w')
        fin = open(sys.argv[1], 'r')
        c_in = csv.reader(fin)
        # discard the headers
        h = next(c_in)


    conflicts_d = md.unpickle_data('conflicts_d.pkl')
    c_out = csv.writer(out_file)
    write_conflicts_csv(conflicts_d, c_in, c_out)
    if c_in:
        fin.close()
        
    out_file.close()
