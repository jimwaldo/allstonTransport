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

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python build_transition_d.py student_schedule_d.pkl')
        sys.exit(2)

    schedule_d = md.unpickle_data(sys.argv[1])
    transition_d = {}

    for k, v in schedule_d.items():
        transition_d[k] = ct.transition(v)

    md.pickle_data('transition_d.pkl', transition_d)

