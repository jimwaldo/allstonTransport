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
    term, class_num, course_id, subject, catalog, section = [str(x).upper().strip() for x in l[:6]]

    return will_be_allston_course_subj_catalog(subject, catalog)


def will_be_allston_course_canonical_cn(cn):
    """
    Given canonical course name, determine whether this 
    course will be taught in Allston in the future.
    :param cn, e.g., "COMPSCI 50"
    :return boolean indicating whether the course will be taught in Alston.
    """
    start = cn.find(' ')
    subject = cn[:start]
    catalog = cn[start+1:]

    assert subject == subject.upper().strip()
    assert catalog == catalog.upper().strip()

    return will_be_allston_course_subj_catalog(subject, catalog)
    
def will_be_allston_course_subj_catalog(subject, catalog):
    """
    Given subject and catalog information about a course, determine whether this 
    course will be taught in Allston in the future.
    :param subject, e.g., "COMPSCI"
    :param catalog, e.g., "50"
    :return boolean indicating whether the course will be taught in Alston.
    """
    #return _all_seas(subject, catalog)
    return _current_best(subject, catalog)
    #return _move_stat_or_econ(subject, catalog)
    
def _current_best(subject, catalog):
    """
    Our current (March 2019) best understanding of what courses will be taught in Allston.
    """

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

    if subject == "APPHY" and catalog in ["50A", "50B"]:
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

def _all_seas(subject, catalog):
    if subject == "APPHY" and catalog ==  "50B":
        return True

    if subject == "ESE":
        return catalog in ["166", "6"]

    return subject in ["COMPSCI", "ENG-SCI", "BE", "APMTH", "APCOMP"]
    
def _move_stat_or_econ(subject, catalog, move_stat = True, move_econ = False):
    if _current_best(subject, catalog):
        return True

    if move_stat and subject == "STAT":
        return True

    if move_econ and subject == "ECON":
        return True
    
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
