#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, May 12 2019

@author chong

Using a CSV file of bad course conflicts and a course schedule, compute a score for how bad
the schedule is in terms of bad course conflicts.
"""

import warnings
import sys, csv
import make_name_dicts as md
import class_time as ct
from allston_course_selector import will_be_allston_course_subj_catalog

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

class course_time(object):
    """
    The object used to represent the time  and days that a course meets
    """

    def __init__(self, time_start, time_end, mon, tue, wed, thu, fri, sat, sun):
        """
        Create an object that represents the time a course is taught.
        """
        self.time_start = ct.normalize_time(time_start)
        self.time_end = ct.normalize_time(time_end)
        self.days = []
        for d in [mon, tue, wed, thu, fri, sat, sun]:
            self.days.append(d == 'Y')

    def __str__(self):
        return self.time_start+"-"+self.time_end + " " + self.days_of_week()


    def days_of_week(self):
        daynames = ['M','Tu','W','Th','F','Sa','Su']
        return "".join([n for (d,n) in zip(self.days, daynames) if d])

    def time_as_interval(self):
        """
        Returns the start and end time as an interval of the number of minutes
        after midnights
        """
        (my_start_h, my_start_m) = ct.time_to_hm(self.time_start)
        (my_end_h, my_end_m) = ct.time_to_hm(self.time_end)

        my_start = my_start_h*60 + my_start_m
        my_end = my_end_h*60 + my_end_m

        assert my_start <= my_end
        
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
    

def build_conflicts_d(csv_in):
    """
    Build a dictionary keyed by canonical course name (e.g. "COMPSCI 50") to dictionaries with 
    a map from canonical course name to number, such that if d[c1][c2] = w, then w is the weight (bigger is worse)
    if courses c1 and c2 conflict.

    :param csv_in: A csv file where the first column is a canonical name,
                   the second column is a canonical name, and the third column is a weight
    :return: a dictionary, as described above.
    """
    conflicts_d = {}
    for l in csv_in:
        (c1, c2, w) = (l[0], l[1], l[2])
        if not (c1 < c2):
            warnings.warn("In file, the course names aren't in alphabetical order: %s is not alphabetically before %s"%(c1,c2))
            (c1, c2) = (c2, c1)

        
        if c1 not in conflicts_d:
            conflicts_d[c1] =  {}

        if c2 in conflicts_d[c1]:
            warnings.warn("Duplicate entry! %s and %s have weights %s and %s"%(c1,c2,conflicts_d[c1][c2],w))

        conflicts_d[c1][c2] = w
                                
    return conflicts_d

def build_course_schedule(csv_in, convert_to_allston=False):
    """
    Build a representation of a course schedule from a CSV file
    input: csv_in is a CSV file (including header row)
    output: course_sched object
    """

    # Read in the headers and try to make sense of them
    h = next(cin)
    cols = {}
    required_cols = [["SUBJECT"], ["CATALOG"], ["Mtg Start","Meeting Start"], ["Mtg End", "Meeting End"], ["Mon"], ["Tues"], ["Wed"], ["Thurs"], ["Fri"], ["Sat"], ["Sun"]]
    optional_cols = [["COMPONENT"]]

    missing = False
    for cs in required_cols:
        found = False
        for c in cs:
            if c.upper() in [t.upper() for t in h]:
                cols[cs[0]] = [t.upper() for t in h].index(c.upper())
                found = True
                break
        if not found:
            warnings.warn("Didn't find column %s in course schedule file"%cs[0])
            missing = True

    if missing:
        sys.exit(1)

    for cs in optional_cols:
        for c in cs:
            if c.upper() in [t.upper() for t in h]:
                cols[cs[0]] = [t.upper() for t in h].index(c.upper())
                break


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
            if component in ["Laboratory", "Discussion", "Conference"]:
                # ignore labs and discussions and other things
                continue

        if start_time == "" or end_time == "":
            # no times, just ignore it
            continue

        cn = canonical_course_name(subj, cat)
        ct = course_time(start_time, end_time, mon, tue, wed, thu, fri, sat, sun)

        if convert_to_allston and will_be_allston_course_subj_catalog(subj, cat):
            ct.convert_to_allston(cn)
        
        if cn not in schedule_d:
            schedule_d[cn] = []

        schedule_d[cn].append(ct)

    return schedule_d


def compute_conflict_score(conflicts_d, sched_d):
    score = 0
    
    for cn1 in conflicts_d:
        for cn2 in conflicts_d[cn1]:
            weight = conflicts_d[cn1][cn2]

            if cn1 not in sched_d:
                #warnings.warn("Course %s is not offered in the schedule"%cn1)
                continue
            if cn2 not in sched_d:
                #warnings.warn("Course %s is not offered in the schedule"%cn2)
                continue
            
            # Let's see if cn1 and cn2 conflict
            if courses_conflict(sched_d[cn1], sched_d[cn2]):
                print("%s and %s conflict (weight %s)! %s and %s"%(cn1,cn2,weight,";".join(str(e) for e in sched_d[cn1]),";".join(str(e) for e in sched_d[cn2])))
                score += float(weight)

    return score

if __name__ == '__main__':
    def usage():
        print('Usage: build_bad_conflict_score_d <bad_course_conflicts.csv> <schedule.csv>')
        sys.exit(1)
        
    if len(sys.argv) != 3:
        usage()


    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning

    conflict_file = sys.argv[1]
    schedule_file = sys.argv[2]

    fin = open(conflict_file, 'r')
    cin = csv.reader(fin)

    # discard first row (which contains headers)
    h = next(cin)

    conflicts_d = build_conflicts_d(cin)    

    fin.close()

    # Now build the schedule file.
    fin = open(schedule_file, 'r')
    cin = csv.reader(fin)
    sched_d = build_course_schedule(cin,convert_to_allston=False)
    fin.close()
    
    # Now compute the score for the schedule
    score = compute_conflict_score(conflicts_d, sched_d)

    res = { "conflict_score": score }

    print("Conflict score is %s"%score)
    md.pickle_data('bad_conflict_score_d.pkl', res)

