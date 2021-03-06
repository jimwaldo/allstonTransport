#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tuesday, Jan 1 2019

@author waldo

Builds a dictionary keyed by student id of all of the classes a student is taking, broken down by day and within
a day by start time. The class schedule record also contains an indicator of where the class is held (either Allston
(a) or Cambridge (c). This will be the dictionary that drives determining how many times each student needs to
travel from cambridge to allson or back, and when those transits happen.
"""

import class_time as cs
import make_name_dicts as md
import sys, csv

def build_sched(csv_in, student_set, class_time_d):
    """
    Build a dictionary keyed by student id with value a student schedule that reflects that classes this student is
    taking.
    :param csv_in: A csv file of the format supplied by the registrar for all of the courses that semester
    :param student_set: The set of students for which a schedule should be constructed
    :param class_time_d: A dictionary indexed by class_num with values course_time objects
    :return: a dictionary indexed by student id with values a student_schedule object
    """
    ret_d = {}
    for l in csv_in:
        if l[8] not in student_set:
            continue

        student= l[8]
        cl = l[1]
        if cl not in class_time_d:
            continue

        class_scheds = class_time_d[cl]
        if student not in ret_d:
            ret_d[student] = cs.student_sched(student)
        for class_sched in class_scheds:
            ret_d[student].add_course(class_sched)

    for s in ret_d.values():
        s.order_classes()

    return ret_d

if __name__ == '__main__':

    def usage():
        print('Usage: build_student_schedule <enrollments.csv>')
        sys.exit(1)

    if len(sys.argv) < 2 or len(sys.argv) > 2:
        usage()

    enrollements_filename = sys.argv[1]
        
    seas_student_set = md.unpickle_data('SEAS_student_set.pkl')
    class_time_d = md.unpickle_data('class_time_d.pkl')

        


    
    fin = open(enrollements_filename, 'r')
    cin = csv.reader(fin)
    h = next(cin)

    student_schedule_d = build_sched(cin, seas_student_set, class_time_d)

    md.pickle_data('student_schedule_d.pkl', student_schedule_d)
    fin.close()

