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
import build_allston_graphs

MIN_COURSES = 2
DROP_NON_ALLSTON_ENROLLMENTS = True

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

        w = int(w)
        if w > 0:
            add_conflict(c1, c2, w)
            add_conflict(c2, c1, w) # add it in the other order, to make it easier to look up...
                                
    return conflicts_d



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
    required_cols = [["HUID"], ["TERM"], ["SUBJECT"], ["CATALOG"]]
    optional_cols = []
    cols = col_index("enrollment data file", h, required_cols, optional_cols)
    

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
            # if "Fall" in term:
            #     warnings.warn("Did not find course %s in the schedule file"%cn)
            continue
        
        if (huid, term) not in scheds_d:
            scheds_d[(huid, term)] = set()
            
        scheds_d[(huid, term)].add(cn)
        

    
    # Now convert it to a dictionary from frozen set of canonical course names (i.e., courses taken in a term) to ints (counting how many students had that set of courses)
    enrollments_d = {}
    for s in scheds_d.values():
        if len(s) < MIN_COURSES:
            # ignore schedules with less than the minimum number of courses
            continue

        if DROP_NON_ALLSTON_ENROLLMENTS:
            if num_allston_courses(s) == 0:
                continue
            
        fs = frozenset(s)        
        if fs not in enrollments_d:
            enrollments_d[fs] = 1
        else:
            enrollments_d[fs] += 1            

    # Output some descriptive stats
    if True:
        print("Multi-year enrollment data: ")
        print("  Total student-semester schedules: %s "%(len(scheds_d)))
        print("  Distinct student-semester schedules: %s "%(len(enrollments_d)))
        hist_d = {}
        for s in scheds_d.values():
            fs = frozenset(s)
            n = num_allston_courses(fs)
            hist_d[n] = hist_d.get(n,0) + 1
        print("  Histogram of number of student semester schedules with number of allston courses: %s "%(hist_d))

        print("  Of these, we are acutally using:")
        hist_d = {}
        total = 0
        for fs in enrollments_d.keys():
            n = num_allston_courses(fs)
            total +=  enrollments_d[fs]
            hist_d[n] = hist_d.get(n,0) + enrollments_d[fs]
        print("      Total student-semester schedules: %s "%(total))
        print("      Distinct student-semester schedules: %s "%(len(enrollments_d)))
        print("      Histogram of number of student semester schedules with number of allston courses: %s "%(hist_d))
        
        
    
    return enrollments_d

def num_allston_courses(cns):
    """
    Given a list of canonical course names cns, 
    how many of them will be in Allston?
    """
    allston_count = 0
    for cn in cns:
        allston_count += 1 if will_be_allston_course_canonical_cn(cn) else 0

    return allston_count

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
                        days[sct.DAYNAMES[i]].append((ct.time_start, ct.time_end, location, cn))
                        # be inefficient and sort the days array every time we add to it...
                        days[sct.DAYNAMES[i]].sort()

        ffs = frozenset(found_courses)
        ss_d[ffs] = days
        
    return ss_d

def compute_conflict_score(conflicts_d, sched_d, courses_to_count=None,print_conflicts=True,large_courses={}):
    score = 0
  
    conflict_output_d = {}
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

            if courses_to_count and not (cn1 in courses_to_count or cn2 in courses_to_count) and not (cn1 in large_courses and cn2 in large_courses):
                # don't bother counting conflicts between cn1 and cn2
                continue
            
            # Let's see if cn1 and cn2 conflict
            if weight > 0 and sct.courses_conflict(sched_d[cn1], sched_d[cn2]):
                s = "  %-12s and %-12s conflict (weight %3s)! %s and %s"%(cn1,cn2,weight,";".join(str(e) for e in sched_d[cn1]),";".join(str(e) for e in sched_d[cn2]))
                conflict_output_d[s] = int(weight)
                score += float(weight)

    # sort and print conflicts
    if print_conflicts:
        print("Conflicts")
        for s in sorted(conflict_output_d.keys(), key= lambda k: conflict_output_d[k]):
            print(s)
    
    return score
            

def count_round_trips(student_schedule_d, enroll_d):
    """
    Given a dictionary of student schedules (see build_student_schedules), returns a dictionary with keys "M", "T", etc., and "week".
    Each key maps to a dictionary from number of round trips to counts of students with that number of round trips on that day, or during that week.
    """
    ret_d = {}
    for dn in sct.DAYNAMES:
        ret_d[dn] = {i:0 for i in range(3)}
    ret_d['week'] = {i:0 for i in range(8)}

    multi_round_trip_blame = {}
    too_few_courses = 0
    
    for fs in student_schedule_d:
        
        num_students = enroll_d.get(fs,0)
        week_count = 0
        for dn in student_schedule_d[fs]:
            lst = student_schedule_d[fs][dn]
            # lst is a list of tuples indicating location

            day_count = 0
            current_loc = "Cambridge"
            for (start, end, loc, cn) in lst:
                if loc != current_loc:
                    current_loc = loc
                    if loc == "Allston":
                        # count a trip to Allston as a round trip (since they need to return eventually to Cambridge)
                        day_count += 1
                        week_count += 1

            if day_count > 1:
                # More than one round trip to Allston in a day :(
                # Blame the Allston courses on that day.
                allston_courses = frozenset({cn for (start, end, loc, cn) in lst if loc == "Allston" })
                if allston_courses not in multi_round_trip_blame:
                    multi_round_trip_blame[allston_courses] = num_students
                else:
                    multi_round_trip_blame[allston_courses] += num_students
                    
            if day_count not in ret_d[dn]:
                ret_d[dn][day_count] = 0
                
            ret_d[dn][day_count] += num_students

        if week_count not in ret_d['week']:
            ret_d['week'][week_count] = 0
        ret_d['week'][week_count] += num_students

    return (ret_d, multi_round_trip_blame)

def count_no_lunches(student_schedule_d, enroll_d, only_allston=False, due_to_allston=False):
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


    def subtract_from_lunch(inter_l, start_time, end_time):
        (start_h, start_m) = ct.time_to_hm(start_time)
        (end_h, end_m) = ct.time_to_hm(end_time)
        inter = (start_h*60 + start_m, end_h*60 + end_m)
        
        assert inter[0] <= inter[1]
        
        return subtract_interval(inter_l, inter)
    
    def has_time_for_lunch(inter_l):
        for (a,b) in inter_l:
            if lunch_duration <= (b-a):
                return True
        return False
    
    too_few_courses = 0

    lunch_blame = {}
    
    for fs in student_schedule_d:
        
        num_students = enroll_d.get(fs,0)
        no_lunch_days = 0

        camb_cns = []
        alls_cns = []
        for cn in fs:
            if will_be_allston_course_canonical_cn(cn):
                alls_cns.append(cn)
            else:
                camb_cns.append(cn)


        if only_allston and len(alls_cns) == 0:
            # check to make sure the courses include at least one allston course_time
            continue

        for dn in student_schedule_d[fs]:
            avail_lunch = [(lunch_start, lunch_end)]
            
            lst = student_schedule_d[fs][dn]
            # lst is a list of tuples indicating times and location

            # Remove cambridge times
            for (start, end, loc, cn) in lst:
                if loc == "Cambridge":
                    avail_lunch = subtract_from_lunch(avail_lunch, start, end)
                else:
                    assert loc == "Allston"

            # Now see if any lunch time remains...

            if not has_time_for_lunch(avail_lunch):
                if not due_to_allston:
                    no_lunch_days += 1
                continue

            assert has_time_for_lunch(avail_lunch)

            # Now remove Allston times
            blame_courses = set()
            for (start, end, loc, cn) in lst:
                if loc == "Allston":
                    new_avail_lunch = subtract_from_lunch(avail_lunch, start, end)
                    if avail_lunch != new_avail_lunch:
                        blame_courses.add(cn)
                    avail_lunch = new_avail_lunch
                    
            if not has_time_for_lunch(avail_lunch):
                no_lunch_days += 1
                fsblame = frozenset(blame_courses)
                lunch_blame[fsblame] = num_students + lunch_blame.get(fsblame, 0)


        ret_d[no_lunch_days] += num_students

    return (ret_d, lunch_blame)

def simple_score(d):
    """
    Produce a simple score that can be compared to other simple scores.
    """

    nl = d['no_lunch_due_to_allston']
    
    # Return a tuple consisting of:
    #  1. Conflict score
    #  2. Sum of 2 or 3 round-trips
    #  3. Weighted sum of no lunch days

    # Given two tuples t1 and t2, t1 is better than t2 if t1 < t2
    return (d['conflict_score'],
            sum([day[2] + day.get(3, 0) for day in d['transport_days'].values()]),
            5.4*nl[5] + 4.3*nl[4] + 3.2*nl[3] + 2.1 * nl[2] + nl[1] + sum([day[1] for day in d['transport_days'].values()]),
            )

def build_schedule_score(sched_d, conflicts_d, enroll_d, courses_to_count = None, print_conflicts=True, large_courses={}):
    # Now get the times for the schedules.
    times_d = build_student_schedules(enroll_d, sched_d)


    # Now compute the conflict score for the schedule
    conflict_score = compute_conflict_score(conflicts_d, sched_d, courses_to_count, print_conflicts,large_courses=large_courses)
    
    # Now compute the number of round trips
    (rt_d, rt_blame) = count_round_trips(times_d, enroll_d)

    total_round_trips = 0
    for key, value in rt_d['week'].items():
        total_round_trips += (key * value)
        
    # Now compute the number of no lunch days
    (nl_d, _) = count_no_lunches(times_d, enroll_d)
    (nl_all_d, _) = count_no_lunches(times_d, enroll_d, only_allston=True)
    (nl_due_to_all_d, lunch_blame) = count_no_lunches(times_d, enroll_d, only_allston=True, due_to_allston=True)

    ret = {}
    ret['conflict_score'] = conflict_score
    ret['transport_days'] = dict(rt_d)
    ret['transport_weeks'] = ret['transport_days']['week']
    del ret['transport_days']['week']
    ret['total_round_trips'] = total_round_trips
    ret['no_lunch'] = nl_d
    ret['no_lunch_allston_students'] = nl_all_d
    ret['no_lunch_due_to_allston'] = nl_due_to_all_d

    ret['simple_score'] = simple_score(ret)
    
    
    return (ret, rt_blame, lunch_blame)

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
    sched_d = sct.build_course_schedule(cin,convert_to_allston=False, filename="schedule_file")
    fin.close()

    # Build the conflict dictionary
    fin = open(conflict_file, 'r')
    cin = csv.reader(fin)
    # discard first row (which contains headers)
    h = next(cin)
    conflicts_d = build_conflicts_d(cin)    
    fin.close()

    
    # Build the student enrollment dictionary
    fin = open(enrollment_file, 'r')
    cin = csv.reader(fin)
    enroll_d = build_enrollment_d(cin, sched_d)
    fin.close()

    (ret, rt_blame, lunch_blame) = build_schedule_score(sched_d, conflicts_d, enroll_d)

    build_allston_graphs.create_graphs(ret)
    print(ret)


    num_allston_courses_d = { i: 0 for i in range(7)}
    for cns, count in enroll_d.items():
        na = num_allston_courses(cns)
        #if na == 4: print("%s has %s allston courses"%(cns,na))
        num_allston_courses_d[na] += count

    print("Here we go! How many Allston courses do student schedules have?")
    print(num_allston_courses_d)
    print("Total is %s"%(sum(num_allston_courses_d.values())))
