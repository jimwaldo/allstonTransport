#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Friday, Jan 04 2019

@author waldo

Builds a list of dictionaries. Each dictionary represents the transitions from Cambridge to Allston or back on a
particular day (0= Monday, 1= Tuesday...). The dictionary is keyed by the start time of the class at the destination,
and the value is the number of students who need to be there at that time. Note that the dictionary does not
distinguish between students moving from Cambridge to Allston from those moving from Allston to Cambridge. The result
is written, as a pickle, to the file trans_time_d_l.pkl in the directory in which the program is run.

The command-line argument is a pickle of a dictionary keyed by student that has the form of the file created by
build_transition_d.py

"""

import sys
import make_name_dicts as md
import class_time as ct

def build_trans_times(transition_d):
    """
    Build a list of dictionaries, one for each day, of times when students are crossing the river, keeping track of the
    number moving from Cambridge to Allston and the number moving from Allston to Cambridge.
    :param transition_d: A dictionary, indexed by student id, of the transitions from one side of the river to the other
    for that student, including both the direction of the transition and the time
    :return: A list of seven dictionaries, one for each day. The dictionaries will be indexed by time with values a pair
    of integers; the first shows the number of students travelling to Allston at that time, the second the number of
    students travelling from Allston to Cambridge at that time.
    """
    trans_time_d = [{},{},{},{},{},{},{}]

    for tran_v in transition_d.values():
        for i in range(0,7):
            times = tran_v.get_trans_times(i)
            out_d = trans_time_d[i]
            for t,v in times.items():
                if t not in out_d:
                    out_d[t] = [0,0]
                if v == 'a':
                    out_d[t][0] += 1
                else:
                    out_d[t][1] += 1
    return trans_time_d

if __name__ == '__main__':
    trans_d = md.unpickle_data('transition_d.pkl')
    trans_time_d = build_trans_times(trans_d)
    md.pickle_data('trans_time_d_l.pkl', trans_time_d)