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
    return _current_best(l)
    #return _legacy(l)

def _current_best(l):
    """
    Our current (March 2019) best understanding of what courses will be taught in Allston.
    """
    term, class_num, course_id, subject, catalog, section = [str(x).upper().strip() for x in l[:6]]

    if subject == "COMPSCI":
        if catalog in ["50","90NCR","90NBR"]:
            # CS50, and the 90 seminars taught in the law school will be in Cambridge
            return False
        # other CS courses will be in Allston
        return True

    if subject == "APCOMP":
        return catalog in ["209A", "227", "298R", "209B", "221", "290R", "297R"]

    if subject == "APMTH":
        return catalog in ["101", "106", "121", "207", "227", "254", "50A", "107", "221", "231"]

    if subject == "APPHY" and catalog ==  "50B":
        return True

    if subject == "BE":
        return catalog in ["110", "121", "125", "128", "129", "130", "191"]

    if subject == "ESE":
        return catalog in ["166", "6"]

    if subject == "ENG-SCI":
        return catalog in ["100HFA", "125", "139", "152", "155", "173", "181", "190", "21",
                           "222", "239", "25", "254", "280", "51", "53", "91HFR", "95R", "96",
                           "112", "120", "123", "150", "151", "156", "177", "183", "201", "22",
                           "221", "23", "23", "230", "234", "249", "26", "277", "298R", "51",
                           "54", "91HFR", "95R", "96"]


    # All other courses will be in Cambridge
    return False

def _legacy(l):
    """
    Implements legacy behavior (the original Waldo approach) of using
    a pickled file of subjects. Hard codes filename :(.
    """
    f_p = open("seas_subject_s.pkl", 'rb')
    seas_subject_s = pickle.load(f_p)
    f_p.close()

    return l[3] in seas_subject_s
