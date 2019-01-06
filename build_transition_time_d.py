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
build_transition_time_d.py

"""

import sys
import make_name_dicts as md
import class_time as ct

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ('Usage: python build_course_times.py transition_d.pkl')
        sys.exit(2)

    trans_d = md.unpickle_data(sys.argv[1])
    trans_time_d = [{}, {}, {}, {}, {}, {}, {}]

    for v in trans_d.values():
        for i in range(0,7):
            times = v.trans_time[i]
            time_d = trans_time_d[i]
            for t in times:
                if t in time_d:
                    time_d[t] += 1
                else:
                    time_d[t] = 1

    md.pickle_data('trans_time_d_l.pkl', trans_time_d)