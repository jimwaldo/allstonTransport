#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday, May 12 2019

@author chong

Some utilities/data structures expressing scheduling slots. Used in the solution of scheduling. 
"""

import scheduling_course_time as sct

# List of sets of slots for classes that meet once per week
ALLSTON_MEETING_TIMES_ONCE_PER_WEEK_ONE_SLOT = (
    ("M1a",),("M2a",),("M3a",),("M4a",),("M5a",),("M6a",),("M7a",),
    ("T1a",),("T2a",),("T3a",),("T4a",),("T5a",),("T6a",),("T7a",),
    ("W1a",),("W2a",),("W3a",),("W4a",),("W5a",),("W6a",),("W7a",),
    ("R1a",),("R2a",),("R3a",),("R4a",),("R5a",),("R6a",),("R7a",),
    ("F1a",),("F2a",),("F3a",),("F4a",),("F5a",),("F6a",),("F7a",))

ALLSTON_MEETING_TIMES_ONCE_PER_WEEK_TWO_SLOTS = (
    ("M1a","M2a"),("M3a","M4a"),("M5a","M6a"),("M6a","M7a"),
    ("T1a","T2a"),("T3a","T4a"),("T5a","T6a"),("T6a","T7a"),
    ("W1a","W2a"),("W3a","W4a"),("W5a","W6a"),("W6a","W7a"),
    ("R1a","R2a"),("R3a","R4a"),("R5a","R6a"),("R6a","R7a"),
    ("F1a","F2a"),("F3a","F4a"),("F5a","F6a"),("F6a","F7a"))

ALLSTON_MEETING_TIMES_TWICE_PER_WEEK = (
    ("M1a","W1a"),("M2a","W2a"),("M3a","W3a"),("M4a","W4a"),("M5a","W5a"),("M6a","W6a"),("M7a","W7a"),
    ("W1a","F1a"),("W2a","F2a"),("W3a","F3a"),("W4a","F4a"),("W5a","F5a"),("W6a","F6a"),("W7a","F7a"),
    ("M1a","F1a"),("M2a","F2a"),("M3a","F3a"),("M4a","F4a"),("M5a","F5a"),("M6a","F6a"),("M7a","F7a"),
    ("T1a","R1a"),("T2a","R2a"),("T3a","R3a"),("T4a","R4a"),("T5a","R5a"),("T6a","R6a"),("T7a","R7a"))

ALLSTON_MEETING_TIMES_TWICE_PER_WEEK_TWO_SLOTS = (
    ("M1a","M2a","W1a","W2a"),("M3a","M4a","W3a","W4a"),("M5a","M6a","W5a","W6a"),
    ("W1a","W2a","F1a","F2a"),("W3a","W4a","F3a","F4a"),("W5a","W6a","F5a","F6a"),
    ("M1a","M2a","F1a","F2a"),("M3a","M4a","F3a","F4a"),("M5a","M6a","F5a","F6a"),
    ("T1a","T2a","R1a","R2a"),("T3a","T4a","R3a","R4a"),("T5a","T6a","R5a","R6a"))

ALLSTON_MEETING_TIMES_THRICE_PER_WEEK = (
    ("M1a","W1a","F1a"),("M2a","W2a","F2a"),("M3a","W3a","F3a"),
    ("M4a","W4a","F4a"),("M5a","W5a","F5a"),("M6a","W6a","F6a"),("M7a","W7a","F7a"))

ALLSTON_MEETING_TIMES = {
    (1,1) : ALLSTON_MEETING_TIMES_ONCE_PER_WEEK_ONE_SLOT,   # Once per week, one slot
    (2,1) : ALLSTON_MEETING_TIMES_TWICE_PER_WEEK,           # Twice per week, one slot
    (3,1) : ALLSTON_MEETING_TIMES_THRICE_PER_WEEK,          # Thrice per week, one slot
    (1,2) : ALLSTON_MEETING_TIMES_ONCE_PER_WEEK_TWO_SLOTS,  # Once per week, two slots
    (2,2) : ALLSTON_MEETING_TIMES_TWICE_PER_WEEK_TWO_SLOTS, # Twice per week, two slots
    }

CAMBRIDGE_SLOT_TIMES = {
    1: ("09:00","10:15"),
    2: ("10:30","11:45"),
    3: ("12:00","13:15"),
    4: ("13:30","14:45"),
    5: ("15:00","16:15"),
    6: ("16:30","17:45"),
    7: ("18:00","19:15"),
    }

ALLSTON_SLOT_TIMES = {
    1: ("09:45","11:00"),
    2: ("11:15","12:30"),
    3: ("12:45","14:00"),
    4: ("14:15","15:30"),
    5: ("15:45","17:00"),
    6: ("17:15","18:30"),
    7: ("18:45","20:00"),
    }

DAYS_OF_WEEK = ("M", "T", "W", "R", "F")

def _assert_is_meeting_time(mt):
    for s in mt:
        _assert_is_slot(s)

def _assert_is_slot(s):
    assert type(s) == str
    assert s[0] in DAYS_OF_WEEK
    assert int(s[1]) in range(1,8)
    if len(s) > 2:
        assert len(s) == 3
        assert s[2] == 'a'

def meeting_time_is_tu_th(mt):
    _assert_is_meeting_time(mt)
    days = set(DAYS_OF_WEEK) & set([s[0] for s in mt])
    return len(days) == len(days & set(("T","R")))

def meeting_frequency(mt):
    _assert_is_meeting_time(mt)
    return len(set([s[0] for s in mt]))

def meeting_time_starts_between_9_and_4(mt):
    _assert_is_meeting_time(mt)
    # is the start slot 1-5 inclusive?
    return min([int(s[1]) for s in mt]) in range(1,6)

def start_time_slot(mt):
    return min([int(s[1]) for s in mt])



    
def meeting_time_to_course_time(mt):
    """
    Convert a meeting time (i.e., a list of strings of the form "M1a", etc") to a sct.course_time.
    Useful for checking conflicts with other scts.
    """
    _assert_is_meeting_time(mt)
    days = list(set(DAYS_OF_WEEK) & set([s[0] for s in mt]))
    times = list(set(range(1,8)) & set([int(s[1]) for s in mt]))

    assert (max(times) - min(times)) in [0,1]
    
    start_time = ALLSTON_SLOT_TIMES[min(times)][0]
    end_time = ALLSTON_SLOT_TIMES[max(times)][1]
    return sct.course_time(start_time,
                           end_time,
                           "M" in days,
                           "T" in days,
                           "W" in days,
                           "R" in days,
                           "F" in days,
                           False, # Saturday
                           False) # Sunday