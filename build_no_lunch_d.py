#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, March 17 2019

@author chong

Using a dictionary of student schedules, counts how many students do not have at least 30 minutes for lunch
between 11am and 2pm.
"""

import make_name_dicts as md
import class_time as ct
import sys

def build_no_lunch_d (st_sched_d):
    """
    Build a dictionary that counts the number of course conflicts for each pair of courses.
    The key to the dictionary is a pair of course_nums, the lower number first, and each
    such pair maps to the count of the number of students with that conflict.
    :param st_sched_d: A dictionary of student schedules
    :return: A dictionary of course conflicts
    """
    no_lunch_d = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}

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

    for k,sched in st_sched_d.items():
        no_lunch_days = 0
        for i in range(0,7):
            # cs is the list courses that the student takes on day i, sorted by start time.

            avail_lunch = [(lunch_start, lunch_end)]
            cs = sched.days[i]
            for sch_en in cs:                
                # get the time interval for sch_en and remove it from avail_lunch
                inter = sch_en.as_interval()
                if inter is not None:
                    avail_lunch = subtract_interval(avail_lunch, inter)

            # Now see if any lunch time remains...
            has_lunch = False
            for (a,b) in avail_lunch:
                if lunch_duration <= (b-a):
                    has_lunch = True

            if not has_lunch:
                no_lunch_days += 1


        no_lunch_d[no_lunch_days] = no_lunch_d[no_lunch_days] + 1


    for k,v in no_lunch_d.items():        
        print("There are %d students that do not have time for lunch on %d days a week"%(v,k))
    return no_lunch_d

if __name__ == '__main__':
    schedule_d = md.unpickle_data('student_schedule_d.pkl')
    no_lunch_d = build_no_lunch_d(schedule_d)
    md.pickle_data('no_lunch_d.pkl', no_lunch_d)

