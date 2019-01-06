#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday, Dec 28 2018

@author waldo

A set of classes that define the data structures used to chart the number and times of crossing the river based
on assuming that the past will reflect the future.
"""

def normalize_time(t):
    '''
    Takes a string representing time as {h}h:mm:ss {AM|PM} and turns it into a 24 hour time of the form hh:mm. This
    will remain a string, but leading zeros will be inserted so that the times sort correctly. This is a reasonably
    disguisting hack, but made necessary by the way the registrar stores times
    :param t: a string representing a time in the form {h}h:mm:ss {AM|PM}
    :return: a string representing the 24 hour representation of the string as hh:mm
    '''
    if t == '':
        return ''

    start = t.find(':')
    hr = t[:start]
    if (t[-2:] == 'PM') and (hr != '12'):
        hold = int(hr)
        hold += 12
        hr = str(hold)
    if len(hr) < 2:
        hr = '0' + hr
    min = t[start:start+3]
    ret_t = hr + min
    return ret_t


class course_time (object):
    '''

    '''
    def __init__(self, csv_line, in_Allston):
        '''

        :param csv_line:
        :param in_Allston:
        '''
        self.class_num = csv_line[1]
        self.time_start = normalize_time(csv_line[8])
        self.time_end = normalize_time(csv_line[9])
        if in_Allston:
            self.where = 'a'
        else:
            self.where = 'c'
        self.days = []
        for i in range(10,17):
            if csv_line[i] == 'Y':
                self.days.append(True)
            else:
                self.days.append(False)

class sched_entry(object):
    '''
    A class that holds the basic information about a class (assumed unique within a semester), including the class
    number, the start and stop times, and whether the class is in Allston ('a') or in Cambridge ('c')
    '''
    def __init__(self, class_num, start_t, end_t, where):
        '''
        Create a schedule entry object
        :param class_num: the number identifying the class
        :param start_t: the start time, in 24 hour format, as a string
        :param end_t: the end time, in 24 hour format, as a string
        :param where: 'a' for Allston, 'c' for Cambridge
        '''
        self.class_num = class_num
        self.start_t = start_t
        self.end_t = end_t
        self.where = where


class student_sched(object):
    '''
    A class that represents a student's schedule over a particular term. Includes the student huid as identifier, a
    set of all the classes the student is taking, and a list of lists of sched_entry objects for each day of the
    week.
    '''
    def __init__(self, student_num):
        '''
        Create a student schedule object, empty except for the student number
        :param student_num: the student id for the student
        '''
        self.student_num = student_num
        self.class_s = set()
        self.days = [[],[],[],[],[],[],[]]

    def add_course(self, course):
        '''
        Add a course to a student_sched. The course will only be added if it has not been previously added. Entries
        will be placed in all of the days that the course meets in the days array
        :param course: a sched_entry object for the course
        :return: None
        '''
        if course.class_num in self.class_s:
            return
        else:
            self.class_s.add(course.class_num)
        entry = sched_entry(course.class_num, course.time_start, course.time_end, course.where)
        for i in range(0,7):
            if course.days[i] == True:
                self.days[i].append(entry)

    def order_classes(self):
        '''
        Sort a day in a student schedule by the start time of the classes
        :return: None
        '''
        for i in range(0,7):
            if len(self.days) > 1:
                self.days[i].sort(key = lambda x:x.start_t)

class transition(object):
    '''
    A class that represents the set of transitions (movements from Cambridge to Allston or back) in a student's schedule.
    This keeps a count for each day, and a sequence of where the student is, along with the times the student needs
    to be at a transition location. This assumes that all students start in Cambridge
    '''
    def __init__(self, s_sched):
        '''
        Build a transition object for a student.
        :param s_sched: a student_sched object containing the student's schedule
        '''
        self.days = [[],[],[],[],[],[],[]]
        self.trans = [0,0,0,0,0,0,0]
        self.trans_time = [[],[],[],[],[],[],[]]
        days = s_sched.days
        for i in range(0,7):
            day = days[i]
            for j in range(0,len(day)):
                self.days[i].append(day[j].where)

        for i in range(0,7):
            day = self.days[i]
            if len(day) > 1:
                where = 'c'
                for j in range(0,len(day)):
                    if day[j] != where:
                        self.trans[i] += 1
                        self.trans_time[i].append(s_sched.days[i][j].start_t)
                        where = day[j]

