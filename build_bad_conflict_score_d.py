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
import scheduling_course_time as sct

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

    def add_conflict(x, y, w):
        if x not in conflicts_d:
            conflicts_d[x] =  {}

        if y in conflicts_d[x]:
            warnings.warn("Duplicate entry! %s and %s have weights %s and %s"%(x,y,conflicts_d[x][y],w))

        conflicts_d[x][y] = w
        
    for l in csv_in:
        (c1, c2, w) = (l[0], l[1], l[2])
        if not (c1 < c2):
            warnings.warn("In file, the course names aren't in alphabetical order: %s is not alphabetically before %s"%(c1,c2))
            (c1, c2) = (c2, c1)

        add_conflict(c1, c2, w)
        add_conflict(c2, c1, w) # add it in the other order, to make it easier to look up...
                                
    return conflicts_d

def build_course_schedule(csv_in, convert_to_allston=False):
    """
    Build a representation of a course schedule from a CSV file
    input: csv_in is a CSV file (including header row)
    output: dictionary from canonical course name to list of sct.course_time objects
    """

    # Read in the headers and try to make sense of them
    h = next(csv_in)
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

        cn = sct.canonical_course_name(subj, cat)
        ct = sct.course_time(start_time, end_time, mon, tue, wed, thu, fri, sat, sun)

        if convert_to_allston and will_be_allston_course_subj_catalog(subj, cat):
            ct.convert_to_allston(cn)
        
        if cn not in schedule_d:
            schedule_d[cn] = []

        schedule_d[cn].append(ct)

    return schedule_d

def output_course_schedule(cout, schedule_d):
    """
    Output the course schedule schedule_d to a CSV file.
    Outputs only a subset of the columns the original file might have had.
    """
    h = ["SUBJECT","CATALOG","Mtg Start","Mtg End","Mon","Tues","Wed","Thurs","Fri","Sat","Sun","Campus"]

    cout.writerow(h)

    
    for cn in schedule_d:
        (subj, catalog) = sct.parse_canonical_course_name(cn)

        campus = "Allston" if will_be_allston_course_subj_catalog(subj, catalog) else "Cambridge"
        cts = schedule_d[cn]
        for ct in cts:            
            days = [ "Y" if d else "N" for d in ct.days ]
            cout.writerow([subj, catalog, ct.time_start, ct.time_end] + days + [campus])
    

def compute_conflict_score(conflicts_d, sched_d):
    score = 0
    
    for cn1 in conflicts_d:
        for cn2 in conflicts_d[cn1]:
            if not (cn1 < cn2):
                continue
            
            weight = conflicts_d[cn1][cn2]

            if cn1 not in sched_d:
                #warnings.warn("Course %s is not offered in the schedule"%cn1)
                continue
            if cn2 not in sched_d:
                #warnings.warn("Course %s is not offered in the schedule"%cn2)
                continue
            
            # Let's see if cn1 and cn2 conflict
            if sct.courses_conflict(sched_d[cn1], sched_d[cn2]):
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

