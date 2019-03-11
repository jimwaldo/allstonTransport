#!/usr/bin/evn python3
# -*- coding: utf-8 -*-
"""
Created on 2019-03-05

@author waldo

Uses a list of dictionaries of times and transitions, created by build_transition_time_d.py, and creates a
csv file with the times and transition. Allows importing into a spreadsheet and easy viewing. An alternative to the
graphical display in display_trans_times.py
"""
import pickle, csv, sys

import display_trans as dt
import make_name_dicts as md

def write_trans_csv(trans_d_l, csv_out):
    """
    From a list (one per day) of dictionaries indexed by time with entries the list of number of students to Allston and
    number of students to Cambridge, write a csv file that contains the table of times and transitions.
    :param trans_d_l: A list of dictionaries of transitions at particular times, as produced by build_transition_time_d.py
    :param csv_out: an open and writeable csv file to which the data is to be written
    :return: None
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    header_l = ['Time', 'To Allston', 'From Allston']
    csv_out.writerow(header_l)
    for i in range(0, len(trans_d_l)):
        csv_out.writerow([days[i]])
        time_l, a_l, c_l = dt.get_time_count_l(trans_d_l[i])
        for j in range(0, len(time_l)):
            csv_out.writerow([time_l[j], a_l[j], c_l[j]])
        csv_out.writerow([''])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print (len(sys.argv))
        print('Usage: python make_csv_transisitons.py out_file.csv')
        sys.exit(1)

    trans_d_l = md.unpickle_data('trans_time_d_l.pkl')
    out_file = open(sys.argv[1], 'w')
    c_out = csv.writer(out_file)
    write_trans_csv(trans_d_l, c_out)
    out_file.close()
