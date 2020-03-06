#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday, Dec 28 2018

@author waldo

A set of classes that define the data structures used to chart the number and times of crossing the river based
on assuming that the past will reflect the future.
"""
from enum import Enum
import warnings

class days(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

START_TIME_CAMBRIDGE = {
    1: "09:00",
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
    1: "09:45",
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
    Takes a string representing time as {h}h:mm{:ss}? {AM|PM} and turns it into a 24 hour time of the form hh:mm. This
    will remain a string, but leading zeros will be inserted so that the times sort correctly. This is a reasonably
    disguisting hack, but made necessary by the way the registrar stores times
    :param t: a string representing a time in the form {h}h:mm{:ss}? {AM|PM}
    :return: a string representing the 24 hour representation of the string as hh:mm
    """
    if t == '':
        return ''

    start = t.find(':')
    hr = t[:start]
    assert hr.isdigit()
    
    ampm = t[-2:].upper()
    assert ampm in ['AM','PM'], "ampm is %s, string is %s"%(ampm, t)
    
    if (ampm == 'PM') and (hr != '12'):
        hold = int(hr)
        hold += 12
        hr = str(hold)
    if len(hr) < 2:
        hr = '0' + hr
    min = t[start:start+3]
    ret_t = hr + min
    return ret_t

def _time_diff(t, u):
    """
    A utility function to compute the difference in minutes 
    between two times in "hh:mm" (24 hour clock) format
    :param t: a string in the form "hh:mm" (24 hour clock)
    :param u: a string in the form "hh:mm" (24 hour clock)
    :return: an integer, the number of minutes difference between t and u. If t is later than u, this number will be negative.
    """
    (th, tm) = time_to_hm(t)
    (uh, um) = time_to_hm(u)
    return (uh*60+um)-(th*60+tm)

def time_to_hm(t):
    """
    A utility function to convert a string in the form  "hh:mm" (24 hour clock)
    to a pair of integers (h, m).
    """
    start = t.find(':')
    hr = t[:start]
    m = t[start+1:start+3]
    return (int(hr), int(m))

def time_as_interval(t, u):
    """
    Given canonical times t and u (where t is earlier than u)
    return a pair (i, j) where i and j are minutes after midnight
    corresponding to t and u
    """
    (my_start_h, my_start_m) = time_to_hm(t)
    (my_end_h, my_end_m) = time_to_hm(u)
    
    my_start = my_start_h*60 + my_start_m
    my_end = my_end_h*60 + my_end_m
    
    assert my_start <= my_end
    
    return (my_start, my_end)


def _add_minutes(t, mins):
    """
    A utility function to add minutes to a time.
    :param t: a string in the form "hh:mm" (24 hour clock)
    :param mins: an integer number of minutes to add to time
    :return: a string in the form "hh:mm" (24 hour clock), which is time + mins minutes
    """
    (hr, m) = time_to_hm(t)
    m = m + int(mins)
    while m > 59:
        m -= 60
        hr = int(hr) + 1

    while hr > 23:
        hr = hr - 24

    # convert them to strings
    hr = str(hr)
    m = str(m)

    if len(hr) < 2:
        hr = '0' + hr
    if len(m) < 2:
        m = '0' + m

    return hr + ":" + m

def is_compliant_cambridge_start_time(start_time):
    return normalize_time(start_time) in START_TIME_CAMBRIDGE.values()

def is_compliant_allston_start_time(start_time):
    return normalize_time(start_time) in START_TIME_ALLSTON.values()

    
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
        if len(csv_line) < 17:
            print("Line too short: %s"%csv_line)
        for i in range(10, 17):
            if csv_line[i] == 'Y':
                self.days.append(True)
            else:
                self.days.append(False)

    def __str__(self):
        return self.class_num + " " + \
            (self.time_start+"-"+self.time_end + " " if self.time_start else "" ) + \
            self.days_of_week() + " " + \
            ("Allston" if self.where == 'a' else "Cambridge")


    def days_of_week(self):
        daynames = ['M','Tu','W','Th','F','Sa','Su']
        return "".join([n for (d,n) in zip(self.days, daynames) if d])
        
    def is_compliant_time(self,where=None):
        """
        Checks whether the course time is compliant with the FAS requirements. Specifically,
        Cambridge courses must start at the times listed in START_TIME_CAMBRIDGE, and Allston
        courses must start at the times listed in START_TIME_ALLSTON.
        We currently only check start times, and do not check other requirements (end times, 
        days of week, etc.)
        """
        if self.time_start == "":
            # no time. We will regard it as compliant...
            return True
 
        if where == None:
            where = self.where

        if where == 'a': 
            return is_compliant_allston_start_time(self.time_start)
        else:
            return is_compliant_cambridge_start_time(self.time_start)

        
    def convert_to_allston(self, course_name=None):
        """
        Convert this course time from a Cambridge time slot to the nearest Allston time slot.
        It will update this object so that the course is now in 
        Allston (self.where == 'a') and the start and end times will be updated to be the
        appropriate corresponding Allston start and end times.
        :return: None
        """
        self.where = "a"
        if self.time_start == "":
            # No start time
            return

        warn_str = None
        if not self.is_compliant_time('c'):
            warn_str = "Converting %s to Allston time, but it is not currently in a Cambridge slot; it is %s-%s."%(course_name,self.time_start,self.time_end)

        # Find the Cambridge timeslot with the minimum distance        
        val, slot = min((abs(_time_diff(t, self.time_start)), slot) for (slot, t) in START_TIME_CAMBRIDGE.items())

        duration = _time_diff(self.time_start, self.time_end)
        
        # Now move it to the corresponding allston slot
        self.time_start = START_TIME_ALLSTON[slot]
        
        # Now update the time_end, by making sure the slot is the same length.
        self.time_end = _add_minutes(self.time_start, duration)

        if warn_str is not None:
            warnings.warn(warn_str + (" Setting it to %s-%s"%(self.time_start,self.time_end)))
            
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
        
    def __str__(self):
        return self.class_num + " " + \
            (self.start_t+"-"+self.end_t + " " if self.start_t else "" ) + \
            ("Allston" if self.where == 'a' else "Cambridge")

    def __eq__(self, other): 
        return self.class_num == other.class_num and \
            self.start_t == other.start_t and \
            self.end_t == other.end_t and \
            self.where == other.where
    
    
    def as_interval(self):
        """
        Returns the start and end time as an interval of the number of minutes
        after midnights
        """
        if self.start_t == "":
            return None
        
        (my_start_h, my_start_m) = time_to_hm(self.start_t)
        (my_end_h, my_end_m) = time_to_hm(self.end_t)

        my_start = my_start_h*60 + my_start_m
        my_end = my_end_h*60 + my_end_m

        assert my_start <= my_end
        
        return (my_start, my_end)
        
    def conflicts_with(self, sch_en):
        """
        Returns boolean indicating whether this schedule entry conflicts
        with the schedule entry sch_en
        """
        if self.start_t == "" or sch_en.start_t == "":
            return False

        if self.class_num == sch_en.class_num:
            # Cannot conflict with itself
            return False

        
        (my_start, my_end) = self.as_interval()
        (oth_start, oth_end) = sch_en.as_interval()

        if my_end <= oth_start or oth_end <= my_start:
            return False

        return True

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
        self.days = [[],[],[],[],[],[],[]]

    def add_course(self, course):
        """
        Add a course to a student_sched. Entries
        will be placed in all of the days that the course meets in the days array
        :param course: a sched_entry object for the course
        :return: None
        """
        entry = sched_entry(course.class_num, course.time_start, course.time_end, course.where)

        for i in range(0,7):
            if course.days[i] == True:
                if entry not in self.days[i]:
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



