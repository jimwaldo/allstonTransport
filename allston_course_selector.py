#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 16:53:00 2019

@author: chong

Defines method will_be_allston_course that determines which courses will be taught on the Allston campus
"""
import sys, pickle

def will_be_allston_course(l):
    """
    Given information about a course, will determine whether this 
    course will be taught in Allston in the future.
    :param l: an array of strings (as read from a CSV file). The first 6 
              columns may be used, and are expected to be:
                0 TERM 
                1 CLASS_NUM
                2 COURSE_ID
                3 SUBJECT
                4 CATALOG
                5 SECTION
              These are the first columns of the generated enrollments.csv 
              and course_times.csv files.
    :return boolean indicating whether the course will be taught in Alston.
    """
    # Currently return the legacy behavior, but this is a hook to programatically have
    # a finer-grain way of determining which courses will be in Allston.
    return _legacy(l)

def _legacy(l):
    """
    Implements legacy behavior (the original Waldo approach) of using
    a pickled file of subjects. Hard codes filename :(.
    """
    f_p = open("seas_subject_s.pkl", 'rb')
    seas_subject_s = pickle.load(f_p)
    f_p.close()

    return l[3] in seas_subject_s
