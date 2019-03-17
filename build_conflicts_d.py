#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, March 17 2019

@author chong

Using a dictionary of student schedules, builds a dictionary that allows calculation of the number of course conflicts
for students. The key to the dictionary is a pair of course_nums, the lower number first, and each
such pair maps to the count of the number of students with that conflict.
"""

import make_name_dicts as md
import class_time as ct
import sys

def build_conflicts_d (st_sched_d):
    """
    Build a dictionary that counts the number of course conflicts for each pair of courses.
    The key to the dictionary is a pair of course_nums, the lower number first, and each
    such pair maps to the count of the number of students with that conflict.
    :param st_sched_d: A dictionary of student schedules
    :return: A dictionary of course conflicts
    """
    ret_d = {}
    total_conflicts = 0
    total_conflict_students = 0
    total_conflict_pairs = 0
    
    for k,sched in st_sched_d.items():
        # Go through the schedule, looking for conflicts
        # Get all the conflict pairs first (so that we don't double
        # count this student for a conflict), and then update the dictionary.
        conflict_pairs = set()
        
        for i in range(0,7):
            # cs is the courses that the student takes on day i
            cs = sched.days[i]
            for c1 in range(len(cs)-1):
                for c2 in range(c1,len(cs)):
                    # get the schedule entries
                    sch_en1 = cs[c1]
                    sch_en2 = cs[c2]
                    if sch_en1.conflicts_with(sch_en2):
                        # the courses conflict!
                        # construct a pair ordered by class_num
                        conflict_pairs.add((min(sch_en1.class_num,sch_en2.class_num),
                                            max(sch_en1.class_num,sch_en2.class_num)))

        # Now increment based on the conflict pairs
        for cp in conflict_pairs:
            total_conflicts += 1
            if cp not in ret_d:
                total_conflict_pairs += 1
                ret_d[cp] = 1
            else:
                ret_d[cp] = ret_d[cp] + 1

        if len(conflict_pairs) > 0:
            total_conflict_students += 1
            
    print(("There are %d pairs of courses that conflict, and " +
          "%d students with a total of %d conflicts")%(total_conflict_pairs, total_conflict_students, total_conflicts))
    return ret_d

if __name__ == '__main__':
    schedule_d = md.unpickle_data('student_schedule_d.pkl')
    conflicts_d = build_conflicts_d(schedule_d)
    md.pickle_data('conflicts_d.pkl', conflicts_d)

