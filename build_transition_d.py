#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday, Jan 4 2019

@author waldo

Using a dictionary of student schedules, builds a dictionary that allows calculation of the transitions from Cambridge
to Allston and back for each student. The key to the dictionary is the student HUID; the value is a transition
object that contains a list for each day of the location of each class for the student, the number of river crossings
for each day, and the times (in order) of the classes for the student. This is the structure that feeds into the
program build_transition_time_d.py that can be used to determine the totals for each day and time.
"""

import make_name_dicts as md
import class_time as ct
import sys

def build_trans_d (st_sched_d):
    """
    Build a transition dictionary for each student. The dictionary will be indexed by the student, and will
    have as value the transition objects from Cambridge to Allston or back for each day of the week and time of
    day for that student
    :param st_sched_d: A dictionary of student schedules
    :return: A dictionary of transitions from one side of the river to the other
    """
    ret_d = {}
    for k,v in st_sched_d.items():
        ret_d[k] = ct.transition(v)

    return ret_d

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python build_transition_d.py student_schedule_d.pkl')
        sys.exit(2)

    schedule_d = md.unpickle_data(sys.argv[1])
    transition_d = build_trans_d(schedule_d)
    md.pickle_data('transition_d.pkl', transition_d)

