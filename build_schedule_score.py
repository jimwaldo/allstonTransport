#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Saturday, May 18 2019

@author chong

Using a course schedule and historic info on student enrollment, compute a score for how bad
the schedule is in terms of round trips to Allston and schedules without lunch.
"""

import warnings
import sys, csv, string
import make_name_dicts as md
import class_time as ct
from allston_course_selector import will_be_allston_course_canonical_cn
import scheduling_course_time as sct
import build_bad_conflict_score_d as bbcsd


MIN_COURSES = 4

def build_enrollment_d(cin, sched_d):
    """
    Build a representation of multi-year enrollment data from a CSV file
    input: cin is a CSV file (including header row). sched_d is a schedule dictionary, which we use to filter out courses we don't know about
    output: dictionary from frozen set of canonical course names (i.e., courses taken in a term) to ints (counting how many students had that set of courses)
    """

    # Read in the headers and try to make sense of them
    h = next(cin)

    # Get rid of unprintable characters in h
    h = [''.join(filter(lambda x: x in string.printable, t)) for t in h]
    cols = {}
    required_cols = [["HUID"], ["TERM"], ["SUBJECT"], ["CATALOG"]]

    missing = False
    for cs in required_cols:
        found = False
        for c in cs:
            if c.upper() in [t.upper() for t in h]:
                cols[cs[0]] = [t.upper() for t in h].index(c.upper())
                found = True
                break
        if not found:
            warnings.warn("Didn't find column %s in enrollment data file"%cs[0])
            missing = True
        
    if missing:
        sys.exit(1)

    # First, build a dictionary from (HUID, term) to course schedules.
    scheds_d = { }

    for l in cin:
        (huid, term, subj, cat) = (l[cols["HUID"]],
                                   l[cols["TERM"]],
                                   l[cols["SUBJECT"]],
                                   l[cols["CATALOG"]])

        if 'Summer' in term:
            # ignore summer term
            continue

        cn = sct.canonical_course_name(subj,cat)

        if cn not in sched_d:
            #XXX!@! warnings.warn("Did not find course %s in the schedule file"%cn)
            continue
        
        if (huid, term) not in scheds_d:
            scheds_d[(huid, term)] = set()
            
        scheds_d[(huid, term)].add(cn)
        

    # Now convert it to a dictionary from frozen set of canonical course names (i.e., courses taken in a term) to ints (counting how many students had that set of courses)
    enrollments_d = {}
    for s in scheds_d.values():
        fs = frozenset(s)        
        if fs not in enrollments_d:
            enrollments_d[fs] = 1
        else:
            enrollments_d[fs] += 1            

    return enrollments_d

def build_student_schedules(enroll_d, sched_d):
    """
    Given a dictionary from frozen set of canonical course names (i.e., courses taken in a term),
    build a dictionary from frozen set of canonical course names to a dictionary from day (string, "M", "T", "W", "Th", "F")
    to the schedule for the day, which is a list of tuples (start, end, location), where start and end are times
    and location is either "Cambridge" or "Allston". That is, the dictionary records for the set of courses,
    where the student needs to be when. The list is sorted by start time.
    TODO: Should we include or ignore conflicts?
    """
    ss_d = {}
    for fs in enroll_d:
        # fs is a set of canonical course names

        days = {}
        
        for dn in sct.DAYNAMES:
            days[dn] = [ ]

        found_courses = []
        
        for cn in fs:
            # cn is a course name
            # sched_d[cn] is a list of sct.course_time objects
            if cn in sched_d:
                found_courses.append(cn)
            else:
                #XXX!@! warnings.warn("Did not find course %s in the schedule file"%cn)
                continue
                
            location = "Allston" if will_be_allston_course_canonical_cn(cn) else "Cambridge"
            for ct in sched_d[cn]:
                for i in range(len(sct.DAYNAMES)):
                    if ct.days[i]:
                        # This course has times on sct.DAYNAMES[i]
                        days[sct.DAYNAMES[i]].append((ct.time_start, ct.time_end, location))
                        # be inefficient and sort the days array every time we add to it...
                        days[sct.DAYNAMES[i]].sort()

        ffs = frozenset(found_courses)
        ss_d[ffs] = days
        
    return ss_d

def count_round_trips(student_schedule_d, enroll_d):
    """
    Given a dictionary of student schedules (see build_student_schedules), returns a dictionary with keys "M", "T", etc., and "week".
    Each key maps to a dictionary from number of round trips to counts of students with that number of round trips on that day, or during that week.
    """
    ret_d = {}
    for dn in sct.DAYNAMES:
        ret_d[dn] = {i:0 for i in range(8)}
    ret_d['week'] = {i:0 for i in range(8)}

    too_few_courses = 0
    
    for fs in student_schedule_d:
        if len(fs) < MIN_COURSES:
            # ignore schedules with less than the minimum number of courses
            too_few_courses += 1
            continue
        
        num_students = enroll_d[fs]
        week_count = 0
        for dn in student_schedule_d[fs]:
            lst = student_schedule_d[fs][dn]
            # lst is a list of tuples indicating location

            day_count = 0
            current_loc = "Cambridge"
            for (start, end, loc) in lst:
                if loc != current_loc:
                    current_loc = loc
                    if loc == "Allston":
                        # count a trip to Allston as a round trip (since they need to return eventually to Cambridge)
                        day_count += 1
                        week_count += 1

            if day_count not in ret_d[dn]:
                ret_d[dn][day_count] = 0
                
            ret_d[dn][day_count] += num_students

        if week_count not in ret_d['week']:
            ret_d['week'][week_count] = 0
        ret_d['week'][week_count] += num_students

    return ret_d

def count_no_lunches(student_schedule_d, enroll_d):
    """
    Given a dictionary of student schedules (see build_student_schedules), returns a dictionary with integer keys (number of days) to number of students with no time for lunch on that many days,
    i.e. no 30 minute break between 
    """
    ret_d = {i:0 for i in range(8)}

    lunch_start = 11*60 # 11AM
    lunch_end = 14*60 # 2PM
    lunch_duration = 30 # 30 minutes for lunch

    def subtract_interval(inter_l, inter):
        """
        An interval is a pair on integers (a,b) such that a < b.
        inter_l is a list of intervals such
        that for (a,b)=inter_l[i] and (c,d)=inter_l[i+1], we have
        b < c. Argument inter is a pair such that we want to remove the interval
        inter from the list of intervals.
        
        For example, if inter_l = [(10,20),(30,40)]  and inter = (15,35), the result
        will be a list [(10,15),(35,40)], i.e., the list now is intervals that do not
        intersect with inter.
        """
        (x,y) = inter
        out = []
        for (a,b) in inter_l:
            if y <= a or x >= b:
                # no intersection!
                out.append((a,b))
                continue

            if  a < x:                
                out.append((a,x))
                
            if y < b:                
                out.append((y,b))

        return out


                
    too_few_courses = 0
    
    for fs in student_schedule_d:
        if len(fs) < MIN_COURSES:
            # ignore schedules with less than the minimum number of courses
            too_few_courses += 1
            continue
        
        num_students = enroll_d[fs]
        no_lunch_days = 0

        for dn in student_schedule_d[fs]:
            avail_lunch = [(lunch_start, lunch_end)]
            
            lst = student_schedule_d[fs][dn]
            # lst is a list of tuples indicating times and location

            for (start, end, loc) in lst:
                (start_h, start_m) = ct.time_to_hm(start)
                (end_h, end_m) = ct.time_to_hm(end)
                inter = (start_h*60 + start_m, end_h*60 + end_m)

                assert inter[0] <= inter[1]
        
                avail_lunch = subtract_interval(avail_lunch, inter)

            # Now see if any lunch time remains...
            has_lunch = False
            for (a,b) in avail_lunch:
                if lunch_duration <= (b-a):
                    has_lunch = True

            if not has_lunch:
                no_lunch_days += 1

        ret_d[no_lunch_days] += num_students

    return ret_d


def build_schedule_score(sched_d, conflicts_d, enroll_d):
    # Now get the times for the schedules.
    times_d = build_student_schedules(enroll_d, sched_d)


    # Now compute the conflict score for the schedule
    conflict_score = bbcsd.compute_conflict_score(conflicts_d, sched_d)
    
    # Now compute the number of round trips
    rt_d = count_round_trips(times_d, enroll_d)

    # Now compute the number of no lunch days
    nl_d = count_no_lunches(times_d, enroll_d)

    ret = {}
    ret['conflict_score'] = conflict_score
    ret['transport_days'] = dict(rt_d)
    ret['transport_weeks'] = ret['transport_days']['week']
    del ret['transport_days']['week']
    ret['no_lunch'] = nl_d
    
    return ret

if __name__ == '__main__':
    def usage():
        print('Usage: build_schedule_score_d.py <schedule.csv> <bad_course_conflicts.csv> <multi-year-enrollment-data.csv>')
        sys.exit(1)
        
    if len(sys.argv) != 4:
        usage()


    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning

    schedule_file = sys.argv[1]
    conflict_file = sys.argv[2]
    enrollment_file = sys.argv[3]

    # Build the schedule file.
    fin = open(schedule_file, 'r')
    cin = csv.reader(fin)
    sched_d = bbcsd.build_course_schedule(cin,convert_to_allston=False)
    fin.close()

    # Build the conflict dictionary
    fin = open(conflict_file, 'r')
    cin = csv.reader(fin)
    # discard first row (which contains headers)
    h = next(cin)
    conflicts_d = bbcsd.build_conflicts_d(cin)    
    fin.close()

    
    # Build the student enrollment dictionary
    fin = open(enrollment_file, 'r')
    cin = csv.reader(fin)
    enroll_d = build_enrollment_d(cin, sched_d)
    fin.close()

    ret = build_schedule_score(sched_d, conflicts_d, enroll_d)

    print(ret)