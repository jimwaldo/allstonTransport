#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday, Dec 28 2018

@author waldo

A set of classes that define the data structures used to chart the number and times of crossing the river based
on assuming that the past will reflect the future.
"""
from enum import Enum

class days(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

START_TIME_CAMBRIDGE = {
    1: "9:00",
    2: "10:30",
    3: "12:00",
    4: "13:30",
    5: "15:00",
    6: "16:30",
    7: "18:00"
}

END_TIME_CAMBRDIGE = {
    1: "10:15",
    2: "11:45",
    3: "13:15",
    4: "14:45",
    5: "16:15",
    6: "17:45",
    7: "19:15"
}

START_TIME_ALLSTON = {
    1: "9:45",
    2: "11:15",
    3: "12:45",
    4: "14:15",
    5: "15:45",
    6: "17:15",
    7: "18:45"
}

END_TIME_ALLSTON = {
    1: "11:00",
    2: "12:30",
    3: "14:00",
    4: "15:30",
    5: "17:00",
    6: "18:30",
    7: "20:00"
}

def normalize_time(t):
    """
    Takes a string representing time as {h}h:mm:ss {AM|PM} and turns it into a 24 hour time of the form hh:mm. This
    will remain a string, but leading zeros will be inserted so that the times sort correctly. This is a reasonably
    disguisting hack, but made necessary by the way the registrar stores times
    :param t: a string representing a time in the form {h}h:mm:ss {AM|PM}
    :return: a string representing the 24 hour representation of the string as hh:mm
    """
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

class course_time(object):
    """
    The object used to represent the time, place, and days that a class meets. The object contains the course_num,
    which is a common identifier for the enrollment and course_time files, the start and stop time for the class
    normalized to a 24-hour clock, the place the class meets (either a for Allston or c for Cambridge) and a list
    of booleans indicating the days on which the course is taught. This is created one-per-course, and used to build
    the student schedules.
    """

    def __init__(self, csv_line, in_Allston):
        """
        Create an object that represents the time and place a course is taught. The object contains the class number,
        which is a common identifier for the enrollment and course_time files, the start and stop time for the class
        normalized to a 24-hour clock, the place the class meets (either a for Allston or c for Cambridge) and a list
        of booleans indicating the days on which the course is taught. This is created one-per-course, and used to build
        the student schedules.
        :param csv_line: a list of values taken from a csv.reader from the course_time file
        :param in_Allston: A boolean indicating if the course is taught in Allston
        """
        self.class_num = csv_line[1]
        self.time_start = normalize_time(csv_line[8])
        self.time_end = normalize_time(csv_line[9])
        if in_Allston:
            self.where = 'a'
        else:
            self.where = 'c'
        self.days = []
        for i in range(10, 17):
            if csv_line[i] == 'Y':
                self.days.append(True)
            else:
                self.days.append(False)

    
    def is_compliant_time(self):
        """
        Checks whether the course time is compliant with the FAS requirements. Specifically,
        Cambridge courses must start at the times listed in START_TIME_CAMBRIDGE, and Allston
        courses must start at the times listed in START_TIME_ALLSTON.
        We currently only check start times, and do not check other requirements (end times, 
        days of week, etc.)
        """
        if self.where == 'a': 
            start_time = START_TIME_ALLSTON
        else:
            start_time = START_TIME_CAMBRIDGE

        # Just do a linear scan through the start times.
        for st in start_time.values():
            if self.time_start == st:
                return True

        return False

    def __add_minutes(t, mins):
        """
        A utility function to add minutes to a time.
        :param t: a string in the form "hh:mm" (24 hour clock)
        :param mins: an integer number of minutes to add to time
        :return: a string in the form "hh:mm" (24 hour clock), which is time + mins minutes
        """
        start = t.find(':')
        hr = t[:start]
        m = t[start+1:start+3]

        m = int(m) + int(mins)
        if m > 59:
            m -= 60
            hr = int(hr) + 1
            
        if int(hr) > 23:
            hr = int(hr) - 24

        # convert them to strings
        hr = str(hr)
        m = str(m)
        
        if len(hr) < 2:
            hr = '0' + hr
        if len(m) < 2:
            m = '0' + m
            
        return hr + ":" + m

        
    def convert_to_allston(self):
        """
        Convert this course time from a Cambridge course to the nearest Allston time slot.
        This method requires that this course is in Cambridge (self.where == 'c') and is a
        compliant course time. It will update this object so that the course is now in 
        Allston (self.where == 'a') and the start and end times will be updated to be the
        appropriate corresponding Allston start and end times.
        :return: None
        """
        assert self.where == 'c', "Course not currently in Cambridge"
        assert self.is_compliant_time(), "Course is not currently in a compliant time slot"

        for (slot, st) in START_TIME_CAMBRIDGE.iteritems():
            if self.time_start == st:
                # We found the start time! Use the slot to get the appropriate start time in Allston
                self.time_start = START_TIME_ALLSTON[slot]
                
                # Now update the time_end. We will hack this by adding 45 minutes. We could
                # probably do something better principled...
                self.time_end = add_minutes(self.time_end, 45)
                return

        raise AssertionError("Failed to find Cambridge start time: " + self.time_s)


class sched_entry(object):
    """
    A class that holds the basic information about a class (assumed unique within a semester), including the class
    number, the start and stop times, and whether the class is in Allston ('a') or in Cambridge ('c'). This is used when
    building the schedule for each student; for each day of the week the class meets, one of these objects will appear
    in the schedule
    """
    def __init__(self, class_num, start_t, end_t, where):
        """
        Create a schedule entry object
        :param class_num: the number identifying the class
        :param start_t: the start time, in 24 hour format, as a string
        :param end_t: the end time, in 24 hour format, as a string
        :param where: 'a' for Allston, 'c' for Cambridge
        """
        self.class_num = class_num
        self.start_t = start_t
        self.end_t = end_t
        self.where = where


class student_sched(object):
    """
    A class that represents a student's schedule over a particular term. Includes the student huid as identifier, a
    set of all the classes the student is taking, and a list of lists of sched_entry objects for each day of the
    week.
    """
    def __init__(self, student_num):
        """
        Create a student schedule object, empty except for the student number
        :param student_num: the student id for the student
        """
        self.student_num = student_num
        self.class_s = set()
        self.days = [[],[],[],[],[],[],[]]

    def add_course(self, course):
        """
        Add a course to a student_sched. The course will only be added if it has not been previously added. Entries
        will be placed in all of the days that the course meets in the days array
        :param course: a sched_entry object for the course
        :return: None
        """
        if course.class_num in self.class_s:
            return
        else:
            self.class_s.add(course.class_num)
        entry = sched_entry(course.class_num, course.time_start, course.time_end, course.where)
        for i in range(0,7):
            if course.days[i] == True:
                self.days[i].append(entry)

    def order_classes(self):
        """
        Sort a day in a student schedule by the start time of the classes
        :return: None
        """
        for i in range(0,7):
            if len(self.days) > 1:
                self.days[i].sort(key = lambda x:x.start_t)

class tr_time(object):
    def __init__(self, tr_to, tr_when):
        self.tr_to = tr_to
        self.tr_when = tr_when


class transition(object):
    """
    A class that represents the set of transitions (movements from Cambridge to Allston or back) in a student's schedule.
    This keeps a count for each day, and a sequence of where the student is, along with the times the student needs
    to be at a transition location. This assumes that all students start in Cambridge
    """
    def __init__(self, s_sched):
        """
        Build a transition object for a student. A transition object contains a list of dictionaries, one for each day,
        of when the student moves from one side of the river to the other. The dictionary is keyed by the time of the
        start of the class to which the student is going, and the value of the dictionary is the location of the class
        ('a' for Allston, 'c' for Cambridge)
        :param s_sched: a student_sched object containing the student's schedule
        """
        self.trans_time = [{}, {}, {}, {}, {}, {}, {}]
        for i in range(0,7):
            day = s_sched.days[i]
            where = 'c'
            for j in range(0,len(day)):
                if day[j].where != where:
                    where = day[j].where
                    s_time = day[j].start_t
                    self.trans_time[i][s_time] = where

    def get_trans_times(self, on_day):
        return self.trans_time[on_day]



