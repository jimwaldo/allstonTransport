#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, May 12 2019

@author chong

Create an Allston schedule that minimizes bad course conflicts.
"""

import warnings
import sys, csv, math
import class_time as ct
from allston_course_selector import will_be_allston_course_subj_catalog
import build_bad_conflict_score_d as bbcsd
import schedule_slots as ss
from ortools.linear_solver import pywraplp
import scheduling_course_time as sct

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
    A Course is a course that needs to be scheduled
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
        """Create vars and constraints for this course"""

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
        """Create/add to objective function for this course"""


        # Put a little pressure on to not use slots 6 or 7
        for asl in self.vars_actualslots:
            if asl[1] == "6":
                objective.SetCoefficient(self.vars_actualslots[asl], 1) 
            if asl[1] == "7":
                objective.SetCoefficient(self.vars_actualslots[asl], 2) 

            # # XXX!@!
            # if asl[0]=="T" and asl[1] in ["4", "5"]:
            #     # avoid any teaching on Tuesday 3pm-5pm
            #     objective.SetCoefficient(self.vars_actualslots[asl], 1000) 
            # # XXX!@!
            # if asl[0]=="F":
            #     # avoid Friday teaching, to mimic faculty preferences
            #     objective.SetCoefficient(self.vars_actualslots[asl], 100) 
            
        
        
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
            objective.SetCoefficient(v_conflicts, float(conflicts_d[self.name][other]))

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
        for s in self.vars_meeting_time:
            if self.vars_meeting_time[s].solution_value():
                return s
        return None

def add_area_constraints(solver, objective, courses):
    """
    Add constraints to spread each area out over days of week and times of day
    """
    areas = ("APCOMP","APMTH","BE","COMPSCI","ENG-SCI","ESE")


    
    for area in areas:
        v_day_of_week_diff = solver.IntVar(0, solver.infinity(), area + " diff between TuTh and MWF courses")
        objective.SetCoefficient(v_day_of_week_diff, 1) 
        
        cn_day_of_week1 = solver.Constraint(0, solver.infinity())
        cn_day_of_week2 = solver.Constraint(0, solver.infinity())
        cn_day_of_week1.SetCoefficient(v_day_of_week_diff, 1)
        cn_day_of_week2.SetCoefficient(v_day_of_week_diff, 1)

        v_time_of_day_diff = solver.IntVar(0, solver.infinity(), area + " diff between times of day")
        objective.SetCoefficient(v_time_of_day_diff, 1) 

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

def solve_schedule(conflicts_d, sched_d, courses_to_schedule_d):
    # Create the solver
    solver = pywraplp.Solver('CSCourseSchedule',
    #                         pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    #                         pywraplp.Solver.BOP_INTEGER_PROGRAMMING)
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

    print('Number of courses to schedule =', len(courses_to_schedule_d))
    print('Number of variables =', solver.NumVariables())
    print('Number of constraints =', solver.NumConstraints())
    print("Starting to solve....")

    result_status = solver.Solve()
    # The problem has an optimal solution.
    print ("Result status: %s"%result_status)
    assert result_status == pywraplp.Solver.OPTIMAL

    # The solution looks legit (when using solvers other than
    # GLOP_LINEAR_PROGRAMMING, verifying the solution is highly recommended!).
    assert solver.VerifySolution(1e-7, True)

    # The objective value of the solution.
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
    for cname in sorted(courses.keys()):
        c = courses[cname]
        s = c.solution_meeting_time()
        print("%-13s scheduled %s"%(cname, ss.meeting_time_to_course_time(s)))

    


if __name__ == '__main__':
    def usage():
        print('Usage: schedule_allston_courses <bad_course_conflicts.csv> <schedule.csv> [-allston-courses <allston_courses_to_schedule.csv>] <output_file.csv>')
        print('  bad_course_conflicts lists the courses that would be bad to schedule at the same time, including a weight of how bad the conflict is')
        print('  schedule.csv is an existing schedule of Harvard courses, both Cambridge and Allston courses. Allston course times will')
        print('                   be ignored, but that set of courses will be used for scheduling (unless -allston-courses is provided)')
        print('  allston_courses_to_schedule is optional, but if provided will be the list of Allston courses to schedule (Allston ')
        print('                   courses in schedule.csv will be ignored)')
        print('  output_file.csv is an output file of Allston schedule times.')
        sys.exit(1)
        


    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning

    args = list(sys.argv[1:])

    remove_allston_courses = True

    allston_file = None
    if "-allston-courses" in args:
        ind = args.index("-allston-courses")
        allston_file = args[ind+1]
        del args[ind:ind+2]


    if len(args) != 3:
        usage()

    conflict_file = args[0]
    schedule_file = args[1]
    output_file = args[2]

    # Build the conflicts file
    fin = open(conflict_file, 'r')
    cin = csv.reader(fin)
    # discard first row (which contains headers)
    h = next(cin)
    conflicts_d = bbcsd.build_conflicts_d(cin)    
    fin.close()

    
    # build the schedule file.
    fin = open(schedule_file, 'r')
    cin = csv.reader(fin)
    sched_d = bbcsd.build_course_schedule(cin)
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
    
    solve_schedule(conflicts_d, sched_d, courses_to_schedule_d)
