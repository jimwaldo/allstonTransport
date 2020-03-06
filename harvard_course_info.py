#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on March 6 2020

@author chong

Code and data to handle specifics of Harvard courses
"""


# #########################
#
# Special lists of courses


# Courses with no lectures. We won't report conflicts with these, or even regard them as "large courses"
no_lecture_courses = ["EXPOS 20", "MATH 1A", "MATH 1B", "MATH 21A", "MATH 21B", "ECON 970", "EXPOS 10", "EXPOS 40",
                      "ENG-SCI 100HFB", "ENG-SCI 91R", "COMPSCI 91R" ]

# #########################
#
# Non-FAS instructor

# Non-FAS instructors can teach on Tuesdays 3-5pm
non_FAS_instructor = ['COMPSCI 109A', 'COMPSCI 109B']

# #########################
#
# Cross listed courses

# This list is the cross-listed courses.
# Each element is a list of cross listed courses, where the first course in the list is the "canonical" course

cross_listed_courses = [
    ['COMPSCI 109A', 'STAT 121A', 'APCOMP 209A'],
    ['COMPSCI 109B', 'STAT 121B', 'APCOMP 209B'],
]

_non_canon = set(c for l in [cl[1:] for cl in cross_listed_courses] for c in l)
def cross_list_canonical(cn):
    for cl in cross_listed_courses:
        if cn in cl:
            return cl[0]

    return cn

def is_cross_list_canonical(cn):
    return cn not in _non_canon