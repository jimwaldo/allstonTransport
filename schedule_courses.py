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
from allston_course_selector import will_be_allston_course_subj_catalog, will_be_allston_course_canonical_cn
from harvard_course_info import cross_list_canonical, is_cross_list_canonical, non_FAS_instructor
import schedule_slots as ss
from ortools.linear_solver import pywraplp
import scheduling_course_time as sct
import build_schedule_score as schedule_score
import build_allston_graphs
import json
import random
import collections


# Note that this file implements three different versions of the solver, controlled by the following variable.
# Version 3 is the recommended version.
# Weights that control the objective function
MAJOR_UNIT = 1000000
MINOR_UNIT = 100

PARAMS =  {
    'WEIGHT_BAD_CONFLICT_FACTOR' : MAJOR_UNIT,

    # area balance and instructor preferences/requirements
    'WEIGHT_AVOID_COURSES_TU_3_TO_5' : MAJOR_UNIT * 500,
    'WEIGHT_FAVOR_COURSES_TU_3_TO_5' : MAJOR_UNIT * -5,
    'WEIGHT_AVOID_COURSES_FRIDAY' : MINOR_UNIT,
    'WEIGHT_AVOID_CS_COURSES_IN_FAC_LUNCH_OR_COLLOQ' : MINOR_UNIT * 10,
    'WEIGHT_DIFF_NUM_COURSES_DAY_OF_WEEK' : MINOR_UNIT,
    'WEIGHT_DIFF_NUM_COURSES_TIME_OF_DAY' : MINOR_UNIT,
    'WEIGHT_AVOID_SLOT_6' : MINOR_UNIT * 200,
    'WEIGHT_AVOID_SLOT_7' : MAJOR_UNIT * 200,

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
    def __init__(self, name, in_allston, frequency, num_slots=None):
        self.name = name
        self.frequency = frequency
        self.num_slots = num_slots

        assert (frequency, num_slots) in ss.ALLSTON_MEETING_TIMES, "Frequency is %s and num slots is %s"%(frequency,num_slots)

        if in_allston:
            self.meeting_times = ss.ALLSTON_MEETING_TIMES[(frequency, num_slots)]
        else:
            self.meeting_times = ss.CAMBRIDGE_MEETING_TIMES[(frequency, num_slots)]
            
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

            if asl=="T4a" or asl=="T5a" or asl=="T5" or asl=="T6":
                if self.name in non_FAS_instructor:
                    # for non-FAS faculty, favor teaching on Tuesday 3pm-5pm
                    if asl == "T5a":
                        objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_FAVOR_COURSES_TU_3_TO_5']*3)
                    else:                        
                        objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_FAVOR_COURSES_TU_3_TO_5'])
                else:
                    # avoid teaching on Tuesday 3pm-5pm for FAS instructors
                    objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_COURSES_TU_3_TO_5'])

            if asl[0]=="F":
                # avoid Friday teaching, to mimic faculty preferences
                objective.SetCoefficient(self.vars_actualslots[asl], PARAMS['WEIGHT_AVOID_COURSES_FRIDAY']) 
            
        
        
        # Add to objective function for bad course conflicts
        for other in conflicts_d.get(self.name, []):
            assert is_cross_list_canonical(other), other

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
                    for aslo in d.vars_actualslots:
                        if sct.courses_conflict([ss.meeting_time_to_course_time([asl])], [ss.meeting_time_to_course_time([aslo])]):
                            # time slots conflict
                            v_both_use_slot = solver.IntVar(0, 1, self.name + " using " + asl + " and " + other + " using " + aslo)
                            makeConjunction(solver, v_both_use_slot, [self.vars_actualslots[asl], d.vars_actualslots[aslo]])
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



    
        
def _guess_course_freq_and_length(cn, cts):
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
        days.update(ct.days_of_week(separator=None))
        (a,b) = ct.time_as_interval()
        lengths.add(int(b-a))
    print("  days are %s and lengths in mins are %s"%(days,lengths))
    numslots = math.ceil(min(lengths)/90)
    if (len(days), numslots) in ss.ALLSTON_MEETING_TIMES:
        print("  using %s times per week for %s slots"%(len(days), numslots))
        return (len(days), numslots)

    warnings.warn("  Course %s meets %s, don't know how to deal with it; ignoring it"%(cn,";".join([str(e) for e in cts])))
    return None

def build_to_schedule_d(csv_in, sched_d):
    """
    Build a dictionary keyed by canonical course name (e.g. "COMPSCI 50") to a pair of numbers (x,y). The courses are the ones we want to schedule
    into Allston slots. The tuple (x,y) means that we would like to schedule the course to meet x times a week for y slots.
    :param csv_in: A csv file where the first column is a canonical name, and the 2nd and third columns are integers.
    :return: a dictionary, as described above.
    """
    to_schedule_d = {}
    for l in csv_in:
        cn = l[0]
        # Check we can parse the course name
        sct.parse_canonical_course_name(cn)

        assert is_cross_list_canonical(cn)

        if cn in to_schedule_d:
            warnings.warn("Duplicate entry! %s listed more than once"%(cn))
            continue
        
        
        if len(l) > 1:
            (x, y) = (int(l[1]), int(l[2]))
            print("Course %s: %s,%s"%(cn,x,y))
            if (x,y) not in [(1,1), (1,2), (2,1), (2,2), (3.1)]:
                warnings.warn("Don't know how to schedule course %s that meets %s a week for %s slots"%(cn,x,y))
                continue
            to_schedule_d[cn] = (x,y)

        else:
            # We weren't given the explicit info for how often the course meets. Try to infer it from the existing schedule
            a = _guess_course_freq_and_length(cn, sched_d[cn])
            if a is not None:
                to_schedule_d[cn] = a
        
                                
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
        assert is_cross_list_canonical(cname)
        in_allston = will_be_allston_course_canonical_cn(cname)
        courses[cname] = Course(cname, in_allston, courses_to_schedule_d[cname][0], courses_to_schedule_d[cname][1])
        courses[cname].createVarsAndConstraints(solver)

    # Now let each course put in its objective function, to avoid bad conflicts
    objective = solver.Objective()
    objective.SetMinimization()

    conflict_vars_d = {}
    
    for cname in courses:
        courses[cname].createObjective(solver, objective, conflict_vars_d, sched_d, conflicts_d, courses)


    add_area_constraints(solver, objective, courses)

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

        
    solver.SetTimeLimit(10 * 1000) # 10 second time limit

    starttime = datetime.datetime.now()
    result_status = solver.Solve()
    endtime = datetime.datetime.now()

    # The problem has an optimal solution.
    # print ("Result status: %s"%result_status)
    # print ("Time: %s seconds"%((endtime-starttime).total_seconds()))

    if result_status == pywraplp.Solver.FEASIBLE:
        # we timed out!
        return None
    
    assert result_status == pywraplp.Solver.OPTIMAL

        
    # The solution looks legit (when using solvers other than
    # GLOP_LINEAR_PROGRAMMING, verifying the solution is highly recommended!).
    assert solver.VerifySolution(1e-7, True)

    return (solver, courses)

class Solution(object):
    """
    Represents a solution, and provides enough info to try new "child solutions"
    i.e., solutions with additional constraints to avoid problematic course scheduling
    """
    def __init__(self, courses, constraints, sched_d, conflicts_d, enroll_d, courses_to_schedule_d, parent=None, was_rand=False,history="",large_courses={}):
        self.parent = parent
        self.was_rand = was_rand
        self.history = history
        self.courses_to_mt_d = {cn : courses[cn].solution_meeting_time() for cn in courses}
        (self.score, rt_blame, lunch_blame) = schedule_score.build_schedule_score(make_sched_d_from_solution(sched_d, self.courses_to_mt_d), conflicts_d, enroll_d, courses_to_count = courses_to_schedule_d, print_conflicts = False, large_courses = large_courses)
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
            cc.append([(cn, self.courses_to_mt_d[cn]) for cn in cs if cn in courses])
            
        for cs in bad_lunch_courses:
            cc.append([(cn, self.courses_to_mt_d[cn]) for cn in cs if cn in courses])


        # remove empty lists
        self.child_constraints = [x for x in cc if x]


def solve_schedule(conflicts_d, sched_d, courses_to_schedule_d, enroll_d,large_courses):
    (solver,courses) = solve_schedule_loop(conflicts_d, sched_d, courses_to_schedule_d, enroll_d)
    
    # For version 3 of the solver, we will find a solution, and then try to incrementally find a better one.
    current_best_soln = Solution(courses, [], sched_d, conflicts_d, enroll_d, courses_to_schedule_d,large_courses = large_courses)
    pending = [current_best_soln]
    loop_count = 0

    print("Call %s is new best: score %s"%(loop_count,current_best_soln.simple_score))

    loop_start = datetime.datetime.now()
    time_limit = datetime.timedelta(minutes=0.15)
    print("Looking for a good solution, will run for %s"%time_limit)
    while pending:
        if (datetime.datetime.now() - loop_start) > time_limit:
            #reached our time limits
            print("Time limit reached! %s"%time_limit)
            break

        # sort pending by simple score
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
                print("---Timed out on child")
                continue
            
            (solver,courses) = res
            csoln = Solution(courses, child_cs, sched_d, conflicts_d, enroll_d,courses_to_schedule_d, parent=s,history="child index %s"%child_index,large_courses = large_courses)
            child_index += 1

            print("    %s:%s"%(loop_count,csoln.simple_score))
            pending.append(csoln)
            
            if csoln.simple_score < current_best_soln.simple_score:
                print("      Call %s is new best: score %s"%(loop_count,csoln.simple_score))
                current_best_soln = csoln
            

    print("History of best solution:")
    sl = current_best_soln
    while sl is not None:
        print("  %s ; %s"%(sl.simple_score,sl.history))
        sl = sl.parent
    print("\n\n")
        
    return current_best_soln.courses_to_mt_d
    
def output_schedule_brief(cout, courses_to_schedule_d, courses_to_mt_d, large_only = False):
    """
    Output a brief version of the schedule, suitable for the Balance tool
    """
    cout.writerow(["CourseCode","DayWeek","Start","End","Campus"])

    # first write out the courses we just scheduled
    for cn in sorted(courses_to_schedule_d.keys()):
        meeting_time = courses_to_mt_d[cn]
        assert is_cross_list_canonical(cn)
        (subj, catalog) = sct.parse_canonical_course_name(cn)

        if print_area and subj != print_area:
            continue

        campus = "Allston" if will_be_allston_course_subj_catalog(subj, catalog) else "Cambridge"
        ct = ss.meeting_time_to_course_time(meeting_time)
        days = ct.days_of_week(separator='/')
        cout.writerow([cn, days, ct.time_start, ct.time_end, campus])

    # Now write out all the other courses
    for cn in sorted(sched_d.keys()):
        assert is_cross_list_canonical(cn)
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
        assert is_cross_list_canonical(cn)
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
        print('Usage: schedule_courses <bad_course_conflicts.csv> <schedule.csv> <multi-year-enrollment-data.csv> [-courses <courses_to_schedule.csv>] [-allallston] [-out <output_file.csv>] [-print AREA | -registrar]')
        print('  bad_course_conflicts lists the courses that would be bad to schedule at the same time, including a weight of how bad the conflict is')
        print('  schedule.csv is an existing schedule of Harvard courses, both Cambridge and Allston courses. ')
        print('  -large-courses is optional, but if provided will be the list of the large courses (used for output and cost computation)')
        print('  -courses is optional, but if provided will be the list of courses to schedule')
        print('  -allallston is optional, but if present will add all Allston courses to the list of courses to be scheduled')
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

    courses_to_schedule_file = process_flag_param_arg(args, "-courses")
    output_file = process_flag_param_arg(args, "-out")
    large_courses_file = process_flag_param_arg(args, "-large-courses")
    print_area = process_flag_param_arg(args, "-print")
    registrar_output = process_flag_arg(args, "-registrar")
    all_allston = process_flag_arg(args, "-allallston")
        

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
    # discard first row (which contains headers).
    h = next(cin)
    conflicts_d = schedule_score.build_conflicts_d(cin)    
    fin.close()

    
    # build the schedule file.
    fin = open(schedule_file, 'r')
    cin = csv.reader(fin)
    sched_d = sct.build_course_schedule(cin, filename=schedule_file)
    fin.close()

    # Build the student enrollment dictionary
    fin = open(enrollment_file, 'r')
    cin = csv.reader(fin)
    enroll_d = schedule_score.build_enrollment_d(cin, sched_d)
    fin.close()
    

    courses_to_schedule_d = collections.OrderedDict()

    if all_allston:
        # Remove any courses from sched_d that will be in Allston
        for cn in list(sched_d.keys()):
            (subj, catalog) = sct.parse_canonical_course_name(cn)
            if will_be_allston_course_subj_catalog(subj, catalog):
                a = _guess_course_freq_and_length(cn, sched_d[cn])
                if a is not None:
                    courses_to_schedule_d[cn] = a

    large_courses = { }
    if large_courses_file is not None:
        # Read in the large courses file
        fin = open(large_courses_file, 'r')
        cin = csv.reader(fin)
        # discard headers
        h = next(cin)
        for l in cin:
            cn = l[0]
            # Check we can parse the course name
            sct.parse_canonical_course_name(cn)

            assert is_cross_list_canonical(cn)

            large_courses[cn] = True

        fin.close()
    
    if courses_to_schedule_file is not None:
        # Read in the courses that we need to find slots for.
        # The first column is the Canonical name. The 2nd and 3rd columns are
        # numbers, x and y, such that we want the course to meet x times per week for y consecutive slots.
        # E.g., a course that meets twice a week for 75 minutes would be x=2, y=1.
        fin = open(courses_to_schedule_file, 'r')
        cin = csv.reader(fin)
        # discard headers
        h = next(cin)

        courses_to_schedule_d.update(build_to_schedule_d(cin, sched_d))
        fin.close()

    if not courses_to_schedule_d:
        print('No courses to be scheduled! Use either -allallston or -courses.')        
        usage()

    print("We will schedule the following courses:")
    for cn, (num_meetings, duration) in courses_to_schedule_d.items():
        print("    %-12s\t(meets %s per week for %s slot)"%(cn, num_meetings, duration))
    
    # Remove courses to schedule from the existing schedule
    for cn in courses_to_schedule_d:
         del sched_d[cn]
    
    courses_to_mt_d = solve_schedule(conflicts_d, sched_d, courses_to_schedule_d, enroll_d,large_courses=large_courses)

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
    (res, rt_blame, lunch_blame) = schedule_score.build_schedule_score(output_sched_d, conflicts_d, enroll_d, courses_to_count = courses_to_schedule_d, print_conflicts = True, large_courses=large_courses)
    print(json.dumps(res, sort_keys=False))

    build_allston_graphs.create_graphs(res)

    # Show the allston courses that we didn't schedule
    print("The following are Allston courses that we kept in their scheduled time")
    for cn in sorted(sched_d.keys()):
        assert is_cross_list_canonical(cn)
        (subj, catalog) = sct.parse_canonical_course_name(cn)

        if will_be_allston_course_subj_catalog(subj, catalog):
            print("    %s"%cn)
            # cts = sched_d[cn]
            # for ct in cts:
            #     days = ct.days_of_week(separator='/')
            #     cout.writerow([cn, days, ct.time_start, ct.time_end, campus])

