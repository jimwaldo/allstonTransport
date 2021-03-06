#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, May 12 2019

@author chong

Utility class and functions for scheduling course times.
"""

import warnings
import sys, csv
import class_time as ct
from allston_course_selector import will_be_allston_course_subj_catalog
from harvard_course_info import cross_list_canonical, is_cross_list_canonical


def canonical_course_name(subject, catalog):
    """
    Put a course name in canonical form (e.g., "ECON 10A")
    XXX copy paste from build_course_pair_stats_d.py, should refactor sometime.
    """
    return (str(subject).strip() + " " + str(catalog).strip()).upper()

def parse_canonical_course_name(cn):
    """
    XXX copy paste from build_course_pair_stats_d.py, should refactor sometime.
    """
    start = cn.find(' ')
    subject = cn[:start]
    catalog = cn[start+1:]

    assert subject == subject.upper().strip()
    assert catalog == catalog.upper().strip()
    
    return (subject, catalog)

DAYNAMES = ['M','T','W',"Th",'F','Sa','Su']

class course_time(object):
    """
    The object used to represent the time  and days that a course meets
    """

    def __init__(self, time_start, time_end, mon, tue, wed, thu, fri, sat, sun, normalized_time = False):
        """
        Create an object that represents the time a course is taught.
        """
        self.time_start = time_start if normalized_time else ct.normalize_time(time_start)
        self.time_end = time_end if normalized_time else ct.normalize_time(time_end)
        self.days = []
        for d in [mon, tue, wed, thu, fri, sat, sun]:
            self.days.append(d == 'Y' or d == True)

    def __str__(self):
        return self.time_start+"-"+self.time_end + " " + self.days_of_week()

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.time_start == other.time_start and
            self.time_end == other.time_end and
            self.days == other.days
        )

    def days_of_week(self, separator=""):
        days = [n for (d,n) in zip(self.days, DAYNAMES) if d]
        if separator is None:
            return days
        return separator.join(days)

    def time_as_interval(self):
        """
        Returns the start and end time as an interval of the number of minutes
        after midnights
        """
        (my_start_h, my_start_m) = ct.time_to_hm(self.time_start)
        (my_end_h, my_end_m) = ct.time_to_hm(self.time_end)

        my_start = my_start_h*60 + my_start_m
        my_end = my_end_h*60 + my_end_m

        assert my_start <= my_end, "Time isn't valid: %s-%s"%(self.time_start, self.time_end)
        
        return (my_start, my_end)
        

    def convert_to_allston(self,coursename=None):
        """
        Convert this course time from a Cambridge time slot to the nearest Allston time slot.
        It will update this object so that the start and end times will be updated to be the
        appropriate corresponding Allston start and end times.
        :return: None
        """
        warn_str = None
        if not ct.is_compliant_cambridge_start_time(self.time_start):
            warn_str = "Converting %s to Allston time, but it is not currently in a Cambridge slot; it is %s-%s."%(coursename,self.time_start,self.time_end)

        # Find the Cambridge timeslot with the minimum distance        
        val, slot = min((abs(ct._time_diff(t, self.time_start)), slot) for (slot, t) in ct.START_TIME_CAMBRIDGE.items())

        (a,b) = self.time_as_interval()
        duration = b-a
        
        # Now move it to the corresponding allston slot
        self.time_start = ct.START_TIME_ALLSTON[slot]
        
        # Now update the time_end, by making sure the slot is the same length.
        self.time_end = ct._add_minutes(self.time_start, duration)

        if warn_str is not None:
            warnings.warn(warn_str + (" Setting it to %s-%s"%(self.time_start,self.time_end)))

    
    def conflicts_with(self, other):
        if (True, True) in zip(self.days, other.days):
            # we intersect on at least one day
            (my_start, my_end) = self.time_as_interval()
            (oth_start, oth_end) = other.time_as_interval()
            return not (my_end <= oth_start or oth_end <= my_start)

        return False

def courses_conflict(sched1, sched2):
    """
    sched1 and sched2 are lists of course_times
    return: true if any of the course times in sched1 overlap with any of the course times in sched2
    """
    for ct1 in sched1:
        for ct2 in sched2:
            if ct1.conflicts_with(ct2):
                return True
    return False
    

def build_course_schedule(csv_in, convert_to_allston=False, filename="some file"):
    """
    Build a representation of a course schedule from a CSV file
    input: csv_in is a CSV file (including header row)
    output: dictionary from canonical course name to list of course_time objects
    """

    def col_index(datafile_desc, headers, required_cols, optional_cols):

        cols = {}

        missing = False
        for cs in required_cols:
            found = False
            for c in cs:
                if c.upper() in [t.upper() for t in headers]:
                    cols[cs[0]] = [t.upper() for t in headers].index(c.upper())
                    found = True
                    break
            if not found:
                warnings.warn("Didn't find column %s in %s with headers %s"%(cs[0], datafile_desc, headers))
                missing = True

        if missing:
            sys.exit(1)

        for cs in optional_cols:
            for c in cs:
                if c.upper() in [t.upper() for t in headers]:
                    cols[cs[0]] = [t.upper() for t in headers].index(c.upper())
                    break

        return cols
    
    # Read in the headers and try to make sense of them
    h = next(csv_in)
    required_cols = [["SUBJECT"], ["CATALOG"], ["Mtg Start","Meeting Start", "MEETING_START"], ["Mtg End", "Meeting End", "MEETING_END"], ["Mon"], ["Tues"], ["Wed"], ["Thurs"], ["Fri"], ["Sat"], ["Sun"]]
    optional_cols = [["COMPONENT"]]
    cols = col_index(filename, h, required_cols, optional_cols)

    schedule_d = { }

    # Now we can go through the rest of the file building up the schedule entries
    for l in csv_in:
        (subj, cat, start_time, end_time, mon, tue, wed, thu, fri, sat, sun) = (l[cols["SUBJECT"]],
                                                                                l[cols["CATALOG"]],
                                                                                l[cols["Mtg Start"]],
                                                                                l[cols["Mtg End"]],
                                                                                l[cols["Mon"]],
                                                                                l[cols["Tues"]],
                                                                                l[cols["Wed"]],
                                                                                l[cols["Thurs"]],
                                                                                l[cols["Fri"]],
                                                                                l[cols["Sat"]],
                                                                                l[cols["Sun"]])
        component = None
        if "COMPONENT" in cols:
            component = l[cols["COMPONENT"]]
            if component in ["Laboratory", "Discussion", "Conference","LAB","DIS","CNC","RR","THE","LRE"]:
                # ignore labs and discussions and other things
                continue
            
        if start_time == "" or end_time == "":
            # no times, just ignore it
            continue

        cn = canonical_course_name(subj, cat)
        cn = cross_list_canonical(cn)
        assert is_cross_list_canonical(cn), cn

        ct = course_time(start_time, end_time, mon, tue, wed, thu, fri, sat, sun)

        if convert_to_allston:
            warnings.warn("Don't currently support convert_to_allston in scheduling_course_time.py function build_course_schedule")
            sys.exit(2)
        # if convert_to_allston and will_be_allston_course_subj_catalog(subj, cat):
        #     ct.convert_to_allston(cn)
        
        if cn not in schedule_d:
            schedule_d[cn] = []

        if ct not in schedule_d[cn]:
            schedule_d[cn].append(ct)

    return schedule_d
