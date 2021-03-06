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

CAMBRIDGE_MEETING_TIMES_ONCE_PER_WEEK_ONE_SLOT = (
    ("M1",),("M2",),("M3",),("M4",),("M5",),("M6",),("M7",),
    ("T1",),("T2",),("T3",),("T4",),("T5",),("T6",),("T7",),
    ("W1",),("W2",),("W3",),("W4",),("W5",),("W6",),("W7",),
    ("R1",),("R2",),("R3",),("R4",),("R5",),("R6",),("R7",),
    ("F1",),("F2",),("F3",),("F4",),("F5",),("F6",),("F7",))

CAMBRIDGE_MEETING_TIMES_ONCE_PER_WEEK_TWO_SLOTS = (
    ("M1","M2"),("M3","M4"),("M5","M6"),("M6","M7"),
    ("T1","T2"),("T3","T4"),("T5","T6"),("T6","T7"),
    ("W1","W2"),("W3","W4"),("W5","W6"),("W6","W7"),
    ("R1","R2"),("R3","R4"),("R5","R6"),("R6","R7"),
    ("F1","F2"),("F3","F4"),("F5","F6"),("F6","F7"))

CAMBRIDGE_MEETING_TIMES_TWICE_PER_WEEK = (
    ("M1","W1"),("M2","W2"),("M3","W3"),("M4","W4"),("M5","W5"),("M6","W6"),("M7","W7"),
    ("W1","F1"),("W2","F2"),("W3","F3"),("W4","F4"),("W5","F5"),("W6","F6"),("W7","F7"),
    ("M1","F1"),("M2","F2"),("M3","F3"),("M4","F4"),("M5","F5"),("M6","F6"),("M7","F7"),
    ("T1","R1"),("T2","R2"),("T3","R3"),("T4","R4"),("T5","R5"),("T6","R6"),("T7","R7"))

CAMBRIDGE_MEETING_TIMES_TWICE_PER_WEEK_TWO_SLOTS = (
    ("M1","M2","W1","W2"),("M3","M4","W3","W4"),("M5","M6","W5","W6"),
    ("W1","W2","F1","F2"),("W3","W4","F3","F4"),("W5","W6","F5","F6"),
    ("M1","M2","F1","F2"),("M3","M4","F3","F4"),("M5","M6","F5","F6"),
    ("T1","T2","R1","R2"),("T3","T4","R3","R4"),("T5","T6","R5","R6"))

CAMBRIDGE_MEETING_TIMES_THRICE_PER_WEEK = (
    ("M1","W1","F1"),("M2","W2","F2"),("M3","W3","F3"),
    ("M4","W4","F4"),("M5","W5","F5"),("M6","W6","F6"),("M7","W7","F7"))

CAMBRIDGE_MEETING_TIMES = {
    (1,1) : CAMBRIDGE_MEETING_TIMES_ONCE_PER_WEEK_ONE_SLOT,   # Once per week, one slot
    (2,1) : CAMBRIDGE_MEETING_TIMES_TWICE_PER_WEEK,           # Twice per week, one slot
    (3,1) : CAMBRIDGE_MEETING_TIMES_THRICE_PER_WEEK,          # Thrice per week, one slot
    (1,2) : CAMBRIDGE_MEETING_TIMES_ONCE_PER_WEEK_TWO_SLOTS,  # Once per week, two slots
    (2,2) : CAMBRIDGE_MEETING_TIMES_TWICE_PER_WEEK_TWO_SLOTS, # Twice per week, two slots
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

def is_allston_slot(s):
    _assert_is_slot(s)
    return len(s) == 3

def is_allston_meeting_time(mt):
    is_allston = is_allston_slot(mt[0])

    # Check that all slots are consistent
    for s in mt:
        assert is_allston_slot(s) == is_allston

    return is_allston

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

def slot_start_time(s):
    _assert_is_slot(s)
    times = CAMBRIDGE_SLOT_TIMES
    if len(s) > 2 and s[2] == 'a':
        times = ALLSTON_SLOT_TIMES
    
    return times[int(s[1])][0]

def slot_end_time(s):
    _assert_is_slot(s)
    times = CAMBRIDGE_SLOT_TIMES
    if len(s) > 2 and s[2] == 'a':
        times = ALLSTON_SLOT_TIMES
    
    return times[int(s[1])][1]

    
def meeting_time_to_course_time(mt):
    """
    Convert a meeting time (i.e., a list of strings of the form "M1a", etc") to a sct.course_time.
    Useful for checking conflicts with other scts.
    """
    _assert_is_meeting_time(mt)
    days = list(set(DAYS_OF_WEEK) & set([s[0] for s in mt]))
    times = list(set(range(1,8)) & set([int(s[1]) for s in mt]))

    assert (max(times) - min(times)) in [0,1]

    slot_times = CAMBRIDGE_SLOT_TIMES
    if is_allston_meeting_time(mt):
        slot_times = ALLSTON_SLOT_TIMES
        
    start_time = slot_times[min(times)][0]
    end_time = slot_times[max(times)][1]
    return sct.course_time(start_time,
                           end_time,
                           "M" in days,
                           "T" in days,
                           "W" in days,
                           "R" in days,
                           "F" in days,
                           False, # Saturday
                           False, # Sunday
                           normalized_time = True)

def distance_between_meeting_times(mt1, mt2):
    """
    Given two meeting times, how many slots apart are they?
    Distance 0 means they have (at least one actual slot) at the same time.
    Distance n means that there is at least one actual slots that is n slots away.
    Returns a positive integer, or None if they are on different days
    """
    min_dist = None
    for asl1 in mt1:
        for asl2 in mt2:
            if asl1[0] != asl2[0]:
                # different days
                continue
            d = abs(int(asl1[1]) - int(asl2[1]))
            if min_dist is None or d < min_dist:
                min_dist = d
    return min_dist