#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, May 12 2019

@author chong

Create an Allston schedule that minimizes bad course conflicts.
"""

import warnings
import sys, csv, math, datetime
import class_time as ct
from allston_course_selector import will_be_allston_course_subj_catalog
import schedule_slots as ss
from ortools.linear_solver import pywraplp
import scheduling_course_time as sct
import build_schedule_score as schedule_score
import build_allston_graphs
import json
import random


# Note that this file implements three different versions of the solver, controlled by the following variable.
# Version 3 is the recommended version.
SOLVER_VERSION = 3
assert SOLVER_VERSION in [1,2,3]

# Weights that control the objective function
PARAMS =  {
    'WEIGHT_BAD_CONFLICT_FACTOR' : 1000000,

    # area balance and instructor preferences/requirements
    'WEIGHT_AVOID_COURSES_TU_3_TO_5' : 10000,
    'WEIGHT_AVOID_COURSES_FRIDAY' : 100,
    'WEIGHT_AVOID_CS_COURSES_IN_FAC_LUNCH_OR_COLLOQ' : 1000,
    'WEIGHT_DIFF_NUM_COURSES_DAY_OF_WEEK' : 100,
    'WEIGHT_DIFF_NUM_COURSES_TIME_OF_DAY' : 100,
    'WEIGHT_AVOID_SLOT_6' : 15000,
    'WEIGHT_AVOID_SLOT_7' : 30000,

    # v1 params
    'WEIGHT_NO_LUNCH_PER_STUDENT' : 0.0001,
    'WEIGHT_PER_STUDENT_TRIP_TO_ALLSTON' : 0.0005,
    'MAX_STUDENT_SCHEDULES' : 1000,

    # v2 params
    'MAX_COURSE_PAIRS' : 20,
    'WEIGHT_COMMON_COURSE_PAIR_ADJACENT_IN_ALLSTON': -2,
    'WEIGHT_COMMON_COURSE_PAIR_ALMOST_ADJACENT_IN_ALLSTON': -1,
    'WEIGHT_COMMON_COURSE_PAIR_DIFF_CAMPUS_DIFF_DAYS': -2,
}


def makeDisjunction(solver, v, disjuncts):
    """
    Add constraints so that variable v is 1 if and only if at least
    one of the variables in disjuncts is 1. (All variables in
    disjuncts and v should be 0-1 valued variables.
    """
    cn = solver.Constraint(0, (len(disjuncts) - 1))
    cn.SetCoefficient(v, len(disjuncts))
    for x in disjuncts:
        cn.SetCoefficient(x, -1)

def makeConjunction(solver, v, conjuncts):
    """
    Add constraints so that variable v is 1 if and only if at least
    all of the variables in disjuncts is 1. (All variables in
    conjuncts and v should be 0-1 valued variables.
    """
    cn = solver.Constraint(0, (len(conjuncts) - 1))
    cn.SetCoefficient(v, -len(conjuncts))
    for x in conjuncts:
        cn.SetCoefficient(x, 1)



class Course:
    """
    A Course is a course that needs to be scheduled. The object
    contains the solver variables for the meeting times and for the actual slots
    that meeting times cover.
    """
    def __init__(self, name, frequency, num_slots=None):
        self.name = name
        self.frequency = frequency
        self.num_slots = num_slots

        assert (frequency, num_slots) in ss.ALLSTON_MEETING_TIMES, "Frequency is %s and num slots is %s"%(frequency,num_slots)

        self.meeting_times = ss.ALLSTON_MEETING_TIMES[(frequency, num_slots)]
                
        self.vars_meeting_time = { }
        self.vars_actualslots = { }

    def createVarsAndConstraints(self, solver):
        """
        Create vars and constraints for this course. The constraints ensure that, e.g.,
        exactly one meeting time is chosen for the course, and that the "actual slot" 
        variables correctly reflect the chosen meeting time.
        """

        # maintain dict from variables for actual slots to variables for meeting_times
        vasl_to_mtx = { }
        
        exactly_one_slot = solver.Constraint(1, 1)

        # One decision variable for each element of this.meeting_times, of which exactly one must be true (=1)
        for s in self.meeting_times:
            
            x = solver.IntVar(0, 1, self.name + " in " +str(s))
            self.vars_meeting_time[s] = x
            exactly_one_slot.SetCoefficient(x, 1)

            actual_slots = list(s)

            # One decision variable for each actual slot
            for asl in actual_slots:
                if asl not in self.vars_actualslots:
                    vasl = solver.IntVar(0, 1, self.name + " in actual " + asl)
                    self.vars_actualslots[asl] = vasl

                vasl = self.vars_actualslots[asl] 
                # Ensure that if x is true (i.e., slot s is chosen) then
                # vasl is true (i.e., we are marked as this course being in this actual slot
                cn = solver.Constraint(0, solver.infinity())
                
                cn.SetCoefficient(x, -1)
                cn.SetCoefficient(vasl, 1)

                if vasl not in vasl_to_mtx:
                    vasl_to_mtx[vasl] = []


                vasl_to_mtx[vasl].append(x)

        # now go through the vasl_to_mtx dict to make sure that vasl is true only if one of its slots is true
        for vasl in vasl_to_mtx:
            cn = solver.Constraint(0, solver.infinity())

            cn.SetCoefficient(vasl, -1)
            for sx in vasl_to_mtx[vasl]:
                cn.SetCoefficient(sx, 1)


    def createObjective(self, solver, objective, conflict_vars_d, sched_d, conflicts_d, courses):
        """
        Create/add to objective function for this course
        """


        # Put a little pressure on to not use slots 6 or 7
        for asl in self.vars_actualslots:
            if asl[1] == "6":
                objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_SLOT_6']) 
            if asl[1] == "7":
                objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_SLOT_7']) 

            if asl[0]=="T" and asl[1] in ["4", "5"]:
                # avoid any teaching on Tuesday 3pm-5pm
                objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_COURSES_TU_3_TO_5']) 

            if asl[0]=="F":
                # avoid Friday teaching, to mimic faculty preferences
                objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_COURSES_FRIDAY']) 
            
        
        
        # Add to objective function for bad course conflicts
        for other in conflicts_d.get(self.name, []):
            if other not in courses and other not in sched_d:
                # we're not scheduling the other course, so we can ignore it
                continue

            if other in courses and not (self.name < other):
                # we will let the processing for the other course handle this weight
                continue

            # create a variable that indicates if self and other conflict, add add the weight
            # to the objective function
            v_conflicts = solver.IntVar(0, 1, self.name + " and " + other + " conflict")
            objective.SetCoefficient(v_conflicts, PARAMS['WEIGHT_BAD_CONFLICT_FACTOR'] * int(conflicts_d[self.name][other]))

            # Record the variable so we can look at it later
            if self.name not in conflict_vars_d:
                conflict_vars_d[self.name] = {}
            assert other not in conflict_vars_d[self.name]
            conflict_vars_d[self.name][other] = v_conflicts

            if other not in courses:
                # the other course already has a fixed schedule.
                # Go through each actual slot and see if it intersects with other course
                disjuncts = []
                for s in self.vars_actualslots:
                    my_course_time = ss.meeting_time_to_course_time([s])
                    
                    if sct.courses_conflict([my_course_time], sched_d[other]):
                        # slots s conflicts with the time for other
                        disjuncts.append(self.vars_actualslots[s])

                if len(disjuncts) > 0:
                    makeDisjunction(solver, v_conflicts, disjuncts)
                
            if other in courses:
                # we are scheduling the other course, so we need to use its variables.
                # Create a variable for each actual slot that indicates if both self and other use that slot.
                d = courses[other]
                vs_d_same_slot = []
                for asl in self.vars_actualslots:
                    if asl in d.vars_actualslots:
                        # actual slot represented by vas is in both courses self and d.
                        v_both_use_slot = solver.IntVar(0, 1, self.name + " and " + other + " using slot " + asl)
                        makeConjunction(solver, v_both_use_slot, [self.vars_actualslots[asl], d.vars_actualslots[asl]])
                        vs_d_same_slot.append(v_both_use_slot)

                if len(vs_d_same_slot) > 0:
                    makeDisjunction(solver, v_conflicts, vs_d_same_slot)            

    def solution_meeting_time(self):
        """
        Return the chosen meeting time for this course. 
        Should be called only after a solution has been found.
        """
        for s in self.vars_meeting_time:
            if self.vars_meeting_time[s].solution_value():
                return s
        return None

def add_area_constraints(solver, objective, courses):
    """
    Add constraints to spread each area out over days of week and times of day
    """
    areas = ("APCOMP","APMTH","BE","COMPSCI","ENG-SCI","ESE")

    # For COMPSCI, avoid Friday lunch (faculty meeting) and Thursday seminar
    for c in courses:
        if not c.startswith("COMPSCI"):
            continue
        for avoid in ["F3a","R5a"]:
            if avoid in courses[c].vars_actualslots:
                objective.SetCoefficient(courses[c].vars_actualslots[avoid], PARAMS['WEIGHT_AVOID_CS_COURSES_IN_FAC_LUNCH_OR_COLLOQ']) 
    
    for area in areas:
        v_day_of_week_diff = solver.IntVar(0, solver.infinity(), area + " diff between TuTh and MWF courses")
        objective.SetCoefficient(v_day_of_week_diff, PARAMS['WEIGHT_DIFF_NUM_COURSES_DAY_OF_WEEK']) 
        
        cn_day_of_week1 = solver.Constraint(0, solver.infinity())
        cn_day_of_week2 = solver.Constraint(0, solver.infinity())
        cn_day_of_week1.SetCoefficient(v_day_of_week_diff, 1)
        cn_day_of_week2.SetCoefficient(v_day_of_week_diff, 1)

        v_time_of_day_diff = solver.IntVar(0, solver.infinity(), area + " diff between times of day")
        objective.SetCoefficient(v_time_of_day_diff, PARAMS['WEIGHT_DIFF_NUM_COURSES_TIME_OF_DAY']) 

        cns_times_of_day = { } # each constraint will be (num in slot i - num in slot j)
        for i in range(1,6):
            cns_times_of_day[i] = { }
            for j in range(1,6):
                if i == j:
                    continue
                cns_times_of_day[i][j] = solver.Constraint(0, solver.infinity())
                cns_times_of_day[i][j].SetCoefficient(v_day_of_week_diff, 1)

                
        for c in courses:
            if not c.startswith(area):
                continue

            for s in courses[c].vars_meeting_time:
                if ss.meeting_frequency(s) in (2,3):
                    vmt = courses[c].vars_meeting_time[s]
                    if ss.meeting_time_is_tu_th(s):
                        cn_day_of_week1.SetCoefficient(vmt, 1)
                        cn_day_of_week2.SetCoefficient(vmt,-1)
                    else:
                        cn_day_of_week1.SetCoefficient(vmt,-1)
                        cn_day_of_week2.SetCoefficient(vmt, 1)

                    if ss.meeting_time_starts_between_9_and_4(s):
                        slot = ss.start_time_slot(s)
                        assert slot in range(1,6), slot
                        for j in range(1,6):
                            if slot == j:
                                continue
                            cns_times_of_day[slot][j].SetCoefficient(vmt, 1)
                            cns_times_of_day[j][slot].SetCoefficient(vmt,-1)



def add_constraints_for_one_student_schedule_day(solver, objective, courses, enroll_d, sched_d, fs, tu_thu):
    # Go through the courses in fs and figure out the important times (i.e., start and end times of the student's courses)
    # For each such time t:
    #     in_cambridge[t] is 0-1 variable and 1 iff the student needs to be in Cambridge at time t
    #     in_allston[t] is 0-1 variable and 1 iff the student needs to be in Allston at time t
    #     location[t] is 0-1 variable and in_allston[t] == 1 => location[t] == 1 and (in_allston[t] == 0 and in_cambridge[t] == 1) => location[t] == 0
    #     scheduled[t] is 0-1 variable and 1 iff the student has a course schedule at time t

    # We separate them out like this because the schedule may
    # have conflicts, and so we just say that the location
    # pays more attention to allston. Think of "in_cambridge"
    # and "in_allston" vars as where the student is meant to
    # be, and "location" vars as where the student actually is.

    # To reduce round trips, we want to minimize the number of
    # t such that location[t] == 1 and location[t-1] == 0
    # (i.e., student has to travel to allston)

    assert SOLVER_VERSION == 1
    
    start_time = 8*60-15 # 7:45am
    end_time = 18*60 # 6pm
    lunch_start = 11*60 # 11AM
    lunch_end = 14*60 # 2PM
    lunch_duration = 30 # 30 minutes for lunch

    allston_course_on_day = False
    
    times = set()

    dayname = "TuThu" if tu_thu else "MWF"
    def is_appropriate_day(mt):
        days = [ss.DAYS_OF_WEEK.index(slot[0]) for slot in mt]
        is_tu_or_thu = 1 in days or 3 in days
        return is_tu_or_thu if tu_thu else (not is_tu_or_thu)
    def is_appropriate_day_cto(cto):
        is_tu_or_thu = cto.days[1] or cto.days[3]
        return is_tu_or_thu if tu_thu else (not is_tu_or_thu)

        
    for cn in fs:
        if cn in courses:
            # cn is in Allston
            for mt in courses[cn].vars_meeting_time:
                if not is_appropriate_day(mt):
                    # wrong day!
                    continue
                course_time = ss.meeting_time_to_course_time(mt)
                (start, end) = ct.time_as_interval(course_time.time_start, course_time.time_end)
                times.add(start)
                times.add(end)
                allston_course_on_day = True
                
        else:
            # cn is in Cambridge
            assert cn in sched_d
            # sched_d[cn] is a list of course_time objects
            for cto in sched_d[cn]:
                if not is_appropriate_day_cto(cto):
                    # wrong day!
                    continue
                (start, end) = ct.time_as_interval(cto.time_start, cto.time_end)
                times.add(start)
                times.add(end)

    if not allston_course_on_day:
        # no courses in allston on this day!
        return

    times.add(0)
    times = sorted(list(times))

    v_in_cambridge = [False for i in range(len(times))]
    v_in_allston = [solver.IntVar(0, 1, "%s: must be in allston at %s on day %s"%(fs,times[i],dayname)) if i > 0 else None for i in range(len(times))]
    v_location = [solver.IntVar(0, 1, "%s: location at %s on day %s"%(fs,times[i],dayname)) for i in range(len(times))]
    v_is_scheduled = [solver.IntVar(0, 1, "%s: is scheduled at %s on day %s"%(fs,times[i],dayname)) if i > 0 else None for i in range(len(times))]

    # force student to be in Cambridge at the start of the day
    v_in_cambridge[0] = True
    cnst = solver.Constraint(0,0)
    cnst.SetCoefficient(v_location[0], 1)                        

    # Set up constraints on location to indicate where the student is
    for t in range(1,len(times)):
        # if v_in_allston[t] is true, then v_location[t] needs to be true
        cnst = solver.Constraint(0, solver.infinity())
        cnst.SetCoefficient(v_in_allston[t], -1)
        cnst.SetCoefficient(v_location[t], 1)

    # Set up objective function to minimize transitions to Allston
    for t in range(1,len(times)):
        v_trans_to_allston = solver.IntVar(0, 1, "%s: transition to allston at %s on day %s"%(fs,times[t],dayname))
        cnst = solver.Constraint(0, solver.infinity())
        cnst.SetCoefficient(v_location[t-1], 1)
        cnst.SetCoefficient(v_location[t], -1)
        cnst.SetCoefficient(v_trans_to_allston, 1)
        objective.SetCoefficient(v_trans_to_allston, PARAMS['WEIGHT_PER_STUDENT_TRIP_TO_ALLSTON'] * int(enroll_d[fs]))


    # Set up objective function to allow students to have lunch
    # Do something simple that just tries to free up time in there.
    lunch_schedule_vars = []
    for t in range(1,len(times)):
        if lunch_start <= times[t] and times[t] < lunch_end:
            lunch_schedule_vars.append(v_is_scheduled[t])
        
    no_lunch = solver.IntVar(0, 1, "%s: no lunch on day %s"%(fs,dayname))
    makeConjunction(solver, no_lunch, lunch_schedule_vars)
    objective.SetCoefficient(no_lunch, PARAMS['WEIGHT_NO_LUNCH_PER_STUDENT'] * int(enroll_d[fs])) 


    # Now go through the courses in fs and set up the constraints on v_in_allston, v_in_cambridge, and v_is_scheduled
    for cn in fs:
        if cn in courses:
            # cn is in Allston
            # Add the appropriate constraints
            for asl in courses[cn].vars_actualslots:
                if not is_appropriate_day([asl]):
                    # wrong day!
                    continue

                (asl_start, asl_end) = ct.time_as_interval(ss.slot_start_time(asl), ss.slot_end_time(asl))

                for t in range(1,len(times)):
                    # does the time represented by asl contain the time times[t]?
                    # if so, constrain v_in_allston[t] to be true if var_actual_slots is true
                    if asl_start <= times[t] and times[t] < asl_end:
                        # if courses[cn].vars_actualslots[asl] then  v_in_allston[t]
                        cnst = solver.Constraint(0, solver.infinity())
                        cnst.SetCoefficient(courses[cn].vars_actualslots[asl], -1)
                        cnst.SetCoefficient(v_in_allston[t], 1)

                        # if courses[cn].vars_actualslots[asl] then  v_is_scheduled[t]
                        cnst = solver.Constraint(0, solver.infinity())
                        cnst.SetCoefficient(courses[cn].vars_actualslots[asl], -1)
                        cnst.SetCoefficient(v_is_scheduled[t], 1)
        else:
            # cn is in Cambridge
            assert cn in sched_d
            # sched_d[cn] is a list of course_time objects
            for cto in sched_d[cn]:
                if not is_appropriate_day_cto(cto):
                    # wrong day!
                    continue
                (cto_start, cto_end) = cto.time_as_interval()
                for t in range(1,len(times)):
                    # does the time represented by cto contain the time times[t]?
                    # if so, constrain v_in_cambridge[t] to be true
                    if cto_start <= times[t] and times[t] < cto_end:
                        if not v_in_cambridge[t]:
                            v_in_cambridge[t] = True
                            cnst = solver.Constraint(1,1)
                            cnst.SetCoefficient(v_is_scheduled[t], 1)                        
                                        
def add_student_schedule_constraints_v1(solver, objective, courses, enroll_d, sched_d):
    """
    Add constraints to minimize round trips, no lunch days, etc. Do this by directly adding constraints
    for each student.
    This approach doesn't actually scale, so it can't be used except for very small numbers of enrolled students.
    """
    assert SOLVER_VERSION == 1
    # enroll_d is a dictionary from frozen set of canonical course
    # names (i.e., courses taken in a term) to ints (counting how many
    # students had that set of courses)

    count = 0

    # go through them in decreasing order of enrollment weight
    for fs in sorted(enroll_d.keys(), key=lambda k: -enroll_d[k]):
        # fs is a set of courses
        if len(fs) < schedule_score.MIN_COURSES:
            # Not enough courses
            continue

        # Make sure at least one of the courses will be in Allston
        in_allston_course_count = 0
        for cn in fs:
            in_allston_course_count += (1 if cn in courses else 0)

        if in_allston_course_count == 0:
            continue


        count += 1
        if count > PARAMS['MAX_STUDENT_SCHEDULES']:
            continue

        #print("  Adding student schedule constraints for %s with weight %s"%(fs,enroll_d[fs]))
        # Go through each day of the week
        #!@!for day in range(5):
        for day in [True, False]: # just do MWF and TR, that's good enough
            add_constraints_for_one_student_schedule_day(solver, objective, courses, enroll_d, sched_d, fs, day)


    print("Total student schedules: %s"%count)

def add_student_schedule_constraints_v2(solver, objective, courses, enroll_d, sched_d):
    """
    Add constraints to minimize round trips, no lunch days, etc. Do this by looking at common course pairs taken by students
    and adding constraints to encourage common Allston pairs to be in adjacent or nearly adjacent meeting times.
    """
    assert SOLVER_VERSION == 2
    # enroll_d is a dictionary from frozen set of canonical course
    # names (i.e., courses taken in a term) to ints (counting how many
    # students had that set of courses)

    # find popular pairs of courses
    pair_count = { }
    for fs in enroll_d:
        ls = sorted(list(fs))
        for i in range(len(ls)):
            for j in range(i+1,len(ls)):
                if ls[i] not in courses and ls[j] not in courses:
                    # both are cambridge courses
                    continue
                
                p = frozenset((ls[i],ls[j]))
                if p not in pair_count:
                    pair_count[p] = enroll_d[fs]
                else:
                    pair_count[p] += enroll_d[fs]

    count = 0
    for p in sorted(pair_count.keys(), key=lambda k: -pair_count[k]):
        if count > PARAMS['MAX_COURSE_PAIRS']:
            break

        count += 1
        (cn1, cn2) = p
        # add constraints for course pair
        if cn1 not in courses:
            (cn1, cn2) = (cn2, cn1)

        # cn1 (and maybe cn2) are Allston courses
        assert cn1 in courses

        print("Processing course pair %s and %s, weight %s"%(cn1,cn2,pair_count[p]))
        
        for mt1 in courses[cn1].vars_meeting_time:
            if cn2 in courses:
                for mt2 in courses[cn2].vars_meeting_time:
                    dist = ss.distance_between_meeting_times(mt1, mt2)
                    if dist == 0:
                        # Hmmm, we probably don't want these in the same slot, but we will let the conflicts constraints handle it
                        continue

                    # !@! try this out, try to vary it
                    if dist in [1,2] and {2,3} != {s[1] for s in mt1+mt2}:
                        # Adjacent (or almost adjacent) and not blocking lunch (slots 2 and 3 in Allston)
                        v = solver.IntVar(0, 1, "%s,%s in %s and %s"%(cn1,cn2,mt1,mt2))
                        makeConjunction(solver, v, [courses[cn1].vars_meeting_time[mt1],courses[cn2].vars_meeting_time[mt2]])
                        weight = PARAMS['WEIGHT_COMMON_COURSE_PAIR_ADJACENT_IN_ALLSTON'] if dist == 1 else PARAMS['WEIGHT_COMMON_COURSE_PAIR_ALMOST_ADJACENT_IN_ALLSTON']
                        objective.SetCoefficient(v, weight * pair_count[p])

            else:
                assert cn2 in sched_d
                # give a bonus if mt1 is all on different days to cn2
                cts = sched_d[cn2]
                days_intersect = False
                for ind in [ss.DAYS_OF_WEEK.index(s[0]) for s in mt1]:
                    for ct in cts:
                        if ct.days[ind]:
                            days_intersect = True
                            break

                if not days_intersect:
                    objective.SetCoefficient(courses[cn1].vars_meeting_time[mt1], PARAMS['WEIGHT_COMMON_COURSE_PAIR_DIFF_CAMPUS_DIFF_DAYS'] * pair_count[p])
                    
        

    
        
def build_to_schedule_d(csv_in):
    """
    Build a dictionary keyed by canonical course name (e.g. "COMPSCI 50") to a pair of numbers (x,y). The courses are the ones we want to schedule
    into Allston slots. The tuple (x,y) means that we would like to schedule the course to meet x times a week for y slots.
    :param csv_in: A csv file where the first column is a canonical name, and the 2nd and third columns are integers.
    :return: a dictionary, as described above.
    """
    to_schedule_d = {}
    for l in csv_in:
        (cn, x, y) = (l[0], int(l[1]), int(l[2]))
        if (x,y) not in [(1,1), (1,2), (2,1), (2,2), (3.1)]:
            warnings.warn("Don't know how to schedule course %s that meets %s a week for %s slots"%(cn,x,y))
            continue

        # Check we can parse the course name
        sct.parse_canonical_course_name(cn)
        
        if cn in to_schedule_d:
            warnings.warn("Duplicate entry! %s listed more than once"%(cn))
            continue
        
        to_schedule_d[cn] = (x,y)
                                
    return to_schedule_d

def solve_schedule_loop(conflicts_d, sched_d, courses_to_schedule_d, enroll_d, constraints = None, loop_count = None):
    """
    Performs one call to the solver to find a schedule.
    loop_count should be unique
    """
    # Create the solver
    solver = pywraplp.Solver('CourseSchedule',
    #                         pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    #                        pywraplp.Solver.BOP_INTEGER_PROGRAMMING)
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    courses = {}
    # Let each constraint create its variables and constraints
    for cname in courses_to_schedule_d:
        courses[cname] = Course(cname, courses_to_schedule_d[cname][0], courses_to_schedule_d[cname][1])
        courses[cname].createVarsAndConstraints(solver)

    # Now let each course put in its objective function, to avoid bad conflicts
    objective = solver.Objective()
    objective.SetMinimization()

    conflict_vars_d = {}
    
    for cname in courses:
        courses[cname].createObjective(solver, objective, conflict_vars_d, sched_d, conflicts_d, courses)


    add_area_constraints(solver, objective, courses)

    if SOLVER_VERSION == 1:
        add_student_schedule_constraints_v1(solver, objective, courses, enroll_d, sched_d)
    elif SOLVER_VERSION == 2:
        add_student_schedule_constraints_v2(solver, objective, courses, enroll_d, sched_d)
    else:
        assert SOLVER_VERSION == 3

    if constraints:
        for cs in constraints:
            # cs is a list of pairs (cn, mt) of canonical course name cn and meeting time mt
            # Add constraints to make sure that we can't have the conjunction of these.
            vars = [courses[cn].vars_meeting_time[mt] for (cn, mt) in cs]
            if vars:
                v = solver.IntVar(0, 1, "Soln count %s constraint %s"%(loop_count, cs))
                makeConjunction(solver, v, vars)
                cnst = solver.Constraint(0, 0)
                cnst.SetCoefficient(v, 1)

        
    if SOLVER_VERSION in [1,2]:
        print('Number of courses to schedule =', len(courses_to_schedule_d))
        print('Number of variables =', solver.NumVariables())
        print('Number of constraints =', solver.NumConstraints())
        print("Starting to solve....")

    if SOLVER_VERSION == 3:
        solver.SetTimeLimit(10 * 1000) # 10 second time limit

    starttime = datetime.datetime.now()
    result_status = solver.Solve()
    endtime = datetime.datetime.now()

    # The problem has an optimal solution.
    if SOLVER_VERSION in [1,2,3]:
        print ("Result status: %s"%result_status)
        print ("Time: %s seconds"%((endtime-starttime).total_seconds()))

    if result_status == pywraplp.Solver.FEASIBLE:
        # we timed out!
        return None
    
    assert result_status == pywraplp.Solver.OPTIMAL

        
    # The solution looks legit (when using solvers other than
    # GLOP_LINEAR_PROGRAMMING, verifying the solution is highly recommended!).
    assert solver.VerifySolution(1e-7, True)

    # The objective value of the solution.
    if SOLVER_VERSION in [1,2]:
        print('Optimal objective value = ' + str(solver.Objective().Value()))
        print()


        # Print out the bad conflicts
        any_conflicts = False
        for cn1 in conflict_vars_d:
            for cn2 in conflict_vars_d[cn1]:
                v = conflict_vars_d[cn1][cn2]
                if v.solution_value():
                    any_conflicts = True
                    print("%s conflicts with %s (badness %s)"%(cn1, cn2, conflicts_d[cn1][cn2]))
        if not any_conflicts:
            print("No bad conflicts!")

        print()
        
        for cname in sorted(courses.keys()):
            c = courses[cname]
            s = c.solution_meeting_time()
            print("%-13s scheduled %s"%(cname, ss.meeting_time_to_course_time(s)))

    return (solver, courses)

class Solution(object):
    """
    Represents a solution, and provides enough info to try new "child solutions"
    i.e., solutions with additional constraints to avoid problematic course scheduling
    """
    def __init__(self, courses, constraints, sched_d, conflicts_d, enroll_d, parent=None, was_rand=False,history=""):
        self.parent = parent
        self.was_rand = was_rand
        self.history = history
        self.courses_to_mt_d = {cn : courses[cn].solution_meeting_time() for cn in courses}
        (self.score, rt_blame, lunch_blame) = schedule_score.build_schedule_score(make_sched_d_from_solution(sched_d, self.courses_to_mt_d), conflicts_d, enroll_d)
        self.simple_score = self.score['simple_score']
        self.constraints = constraints

        bad_rt_courses = sorted(list(rt_blame.keys()), key=lambda k:rt_blame[k], reverse = True)
        # bad_rt_courses is a list of sets of courses that caused multiple Allston round trips, sorted with the worst first.
        # Just take a few of them
        bad_rt_courses = bad_rt_courses[:3]

        bad_lunch_courses = sorted(list(lunch_blame.keys()), key=lambda k:lunch_blame[k], reverse = True)
        # bad_lunch_courses is a list of sets of courses that caused students to miss lunch, sorted with the worst first.
        # Just take a few of them
        bad_lunch_courses = bad_lunch_courses[:3]
        
        # Set up the constraints for child solutions.
        # Needs to be a list of list of pairs (cn, mt) of canonical course name cn and meeting time mt
        cc = []
        for cs in bad_rt_courses:
            cc.append([(cn, self.courses_to_mt_d[cn]) for cn in cs])
            
        for cs in bad_lunch_courses:
            cc.append([(cn, self.courses_to_mt_d[cn]) for cn in cs])

        self.child_constraints = cc


def solve_schedule(conflicts_d, sched_d, courses_to_schedule_d, enroll_d):
    (solver,courses) = solve_schedule_loop(conflicts_d, sched_d, courses_to_schedule_d, enroll_d)
    
    if SOLVER_VERSION in [1,2]:
        return {cn : courses[cn].solution_meeting_time() for cn in courses}

    # For version 3 of the solver, we will find a solution, and then try to incrementally find a better one.
    current_best_soln = Solution(courses, [], sched_d, conflicts_d, enroll_d)
    pending = [current_best_soln]
    loop_count = 0

    print("Call %s is new best: score %s"%(loop_count,current_best_soln.simple_score))

    loop_start = datetime.datetime.now()
    time_limit = datetime.timedelta(minutes=10)
    print("Looking for a good solution, will run for %s"%time_limit)
    while pending:
        if (datetime.datetime.now() - loop_start) > time_limit:
            #reached our time limits
            print("Time limit reached! %s"%time_limit)
            break

        # some of the time, pick a random solution to expand, otherwise, pick the best of the queue
        if False: #!@!random.randrange(100) < 20:
            s = pending.pop(random.randrange(len(pending)))
            was_rand = True
        else:
            # sort pending by simple score
            was_rand = False
            pending.sort(key=lambda x: x.simple_score)            
            s = pending.pop(0)
            # cull
            pending = pending[:200]


        # Expand the children of s
        child_index = 0
        for cc in s.child_constraints:
            child_cs = list(s.constraints)
            child_cs.append(cc)

            loop_count += 1
            
            res = solve_schedule_loop(conflicts_d, sched_d, courses_to_schedule_d, enroll_d, constraints = child_cs, loop_count = loop_count)
            if res is None:
                # we timed out
                continue
            
            (solver,courses) = res
            csoln = Solution(courses, child_cs, sched_d, conflicts_d, enroll_d,parent=s,was_rand=was_rand,history="child index %s"%child_index)
            child_index += 1
            if csoln.simple_score < current_best_soln.simple_score:
                print("Call %s is new best: score %s"%(loop_count,csoln.simple_score))
                current_best_soln = csoln

            print("%s:%s"%(loop_count,csoln.simple_score))
            pending.append(csoln)
            

    print("History of best solution:")
    sl = current_best_soln
    while sl is not None:
        print("  %s ; child of rand selection? %s; %s"%(sl.simple_score,sl.was_rand,sl.history))
        sl = sl.parent
        
    return current_best_soln.courses_to_mt_d
    
def output_schedule_brief(cout, courses_to_schedule_d, courses_to_mt_d):
    """
    Output a brief version of the schedule, suitable for the Balance tool
    """
    cout.writerow(["CourseCode","DayWeek","Start","End","Campus"])

    # first write out the courses we just scheduled
    for cn in sorted(courses_to_schedule_d.keys()):
        meeting_time = courses_to_mt_d[cn]
        (subj, catalog) = sct.parse_canonical_course_name(cn)

        if print_area and subj != print_area:
            continue

        campus = "Allston" if will_be_allston_course_subj_catalog(subj, catalog) else "Cambridge"
        ct = ss.meeting_time_to_course_time(meeting_time)
        days = ct.days_of_week(separator='/')
        cout.writerow([cn, days, ct.time_start, ct.time_end, campus])

    # Now write out all the other courses
    for cn in sorted(sched_d.keys()):
        (subj, catalog) = sct.parse_canonical_course_name(cn)
        if print_area and subj != print_area:
            continue

        campus = "Allston" if will_be_allston_course_subj_catalog(subj, catalog) else "Cambridge"
        cts = sched_d[cn]
        for ct in cts:
            days = ct.days_of_week(separator='/')
            cout.writerow([cn, days, ct.time_start, ct.time_end, campus])

def make_sched_d_from_solution(schedule_d, courses_to_mt_d):
    # create a dictionary of all the courses.
    allcourses = dict(schedule_d)

    for cn in courses_to_mt_d:
        meeting_time = courses_to_mt_d[cn]
        (subj, catalog) = sct.parse_canonical_course_name(cn)
        ct = ss.meeting_time_to_course_time(meeting_time)
        allcourses[cn] = [ct]

    return allcourses

def output_schedule_registrar(cout, schedule_d, courses_to_mt_d):
    """
    Output a version of the schedule, similar to the format supplied by the registerar.
    """

    schedule_score.output_course_schedule(cout, make_sched_d_from_solution(schedule_d, courses_to_mt_d))

            
if __name__ == '__main__':
    def usage():
        print('Usage: schedule_allston_courses <bad_course_conflicts.csv> <schedule.csv> <multi-year-enrollment-data.csv> [-allston-courses <allston_courses_to_schedule.csv>] [-out <output_file.csv>] [-print AREA | -registrar]')
        print('  bad_course_conflicts lists the courses that would be bad to schedule at the same time, including a weight of how bad the conflict is')
        print('  schedule.csv is an existing schedule of Harvard courses, both Cambridge and Allston courses. Allston course times will')
        print('                   be ignored, but that set of courses will be used for scheduling (unless -allston-courses is provided)')
        print('  allston_courses_to_schedule is optional, but if provided will be the list of Allston courses to schedule (Allston ')
        print('                   courses in schedule.csv will be ignored)')
        print('  output_file.csv is an output file of schedule times.')
        print('  -print AREA will only output results for the given area (e.g., "COMPSCI")')
        print('  -registrar will produce output in a similar format to the registrar course schedule output')
        
        sys.exit(1)
        

    def process_flag_arg(args, flag):
        if flag in args:
            ind = args.index(flag)
            del args[ind]
            return True
        return False

    def process_flag_param_arg(args, flag):
        if flag in args:
            ind = args.index(flag)
            res = args[ind+1]
            del args[ind:ind+2]
            return res
        return None
              

    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning

    args = list(sys.argv[1:])

    remove_allston_courses = True

    allston_file = process_flag_param_arg(args, "-allston-courses")
    output_file = process_flag_param_arg(args, "-out")
    print_area = process_flag_param_arg(args, "-print")
    registrar_output = process_flag_arg(args, "-registrar")
        

    if len(args) != 3:
        usage()


    print("\n\n\nRunning %s"%(' '.join(sys.argv)))
    print("Params:")
    print(json.dumps(PARAMS, indent=4, sort_keys=False))
    conflict_file = args[0]
    schedule_file = args[1]
    enrollment_file = args[2]

    # Build the conflicts file
    fin = open(conflict_file, 'r')
    cin = csv.reader(fin)
    # discard first row (which contains headers)
    h = next(cin)
    conflicts_d = schedule_score.build_conflicts_d(cin)    
    fin.close()

    
    # build the schedule file.
    fin = open(schedule_file, 'r')
    cin = csv.reader(fin)
    sched_d = schedule_score.build_course_schedule(cin)
    fin.close()

    # Build the student enrollment dictionary
    fin = open(enrollment_file, 'r')
    cin = csv.reader(fin)
    enroll_d = schedule_score.build_enrollment_d(cin, sched_d)
    fin.close()
    

    def guess_freq_and_length(cn, cts):
        """
        cts is a list of sct.course_time objects
        Guess how many times it meets, and for how many slots.
        """
        if len(cts) == 1:
            freq = len([b for b in cts[0].days if b])
            (a,b) = cts[0].time_as_interval()
            length = math.ceil((b-a)/90)
            if (freq,length) not in ss.ALLSTON_MEETING_TIMES:
                warnings.warn("Course %s meets %s times per week for %s slots, don't know how to deal with it; ignoring it"%(cn,freq,length))
                return None
            return (freq, length)

        
        print("%s is in existing schedule as %s"%(cn,";".join([str(e) for e in cts])))
        days = set()
        lengths = set()
        for ct in cts:
            days.update(ct.days_of_week())
            (a,b) = ct.time_as_interval()
            lengths.add(int(b-a))
        print("  days are %s and lengths in mins are %s"%(days,lengths))
        numslots = math.ceil(min(lengths)/90)
        if (len(days), numslots) in ss.ALLSTON_MEETING_TIMES:
            print("  using %s times per week for %s slots"%(len(days), numslots))
            return (len(days), numslots)

        warnings.warn("  Course %s meets %s, don't know how to deal with it; ignoring it"%(cn,";".join([str(e) for e in cts])))
        return None

    courses_to_schedule_d = { }
    # Remove any courses from sched_d that will be in Allston
    for cn in list(sched_d.keys()):
        (subj, catalog) = sct.parse_canonical_course_name(cn)
        if will_be_allston_course_subj_catalog(subj, catalog):
            a = guess_freq_and_length(cn, sched_d[cn])
            if a is not None:
                courses_to_schedule_d[cn] = a
            del sched_d[cn]

    if allston_file is not None:
        # Read in the courses that we need to find Allston slots for.
        # The first column is the Canonical name. The 2nd and 3rd columns are
        # numbers, x and y, such that we want the course to meet x times per week for y consecutive slots.
        # E.g., a course that meets twice a week for 75 minutes would be x=2, y=1.
        fin = open(allston_file, 'r')
        cin = csv.reader(fin)
        # discard headers
        h = next(cin)

        courses_to_schedule_d = build_to_schedule_d(cin)
        fin.close()

    # Check that courses_to_schedule are not already in the fixed schedule
    for cn in courses_to_schedule_d:
        assert cn not in sched_d, "%s is to be scheduled, but is already in %s"%(cn,schedule_file)
    
    courses_to_mt_d = solve_schedule(conflicts_d, sched_d, courses_to_schedule_d, enroll_d)

    if output_file:
        # Output the combined schedule to the output file
        fout = open(output_file, 'w')
        cout = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if registrar_output:
            output_schedule_registrar(cout, sched_d, courses_to_mt_d)
        else:
            output_schedule_brief(cout, courses_to_schedule_d, courses_to_mt_d)
            
        fout.close()


    output_sched_d = make_sched_d_from_solution(sched_d, courses_to_mt_d)
    (res, rt_blame, lunch_blame) = schedule_score.build_schedule_score(output_sched_d, conflicts_d, enroll_d)
    print(json.dumps(res, sort_keys=False))

    build_allston_graphs.create_graphs(res)
