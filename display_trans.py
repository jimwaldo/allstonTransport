#!/usr/bin/evn python3
# -*- coding: utf-8 -*-
"""
Created on 2019-01-06

@author waldo

"""
import class_time as ct
import make_name_dicts as mnd
import numpy as np
import matplotlib.pyplot as plt
import sys

def get_time_count_l(trans_d):
    """
    Takes a dictionary keyed by class start time with values a list of [students_to_Allston, students_to_Cambridge]
    and creates three lists that can be used to display this information.
    :param trans_d: a dictionary keyed by class start time with values [to_Allston, to_Cambridge]
    :return: three lists; the first is of class start times, the second students moving from Cambridge to Allston, the
    third students moving from Allston to Cambridge
    """
    count_a = []
    count_c = []

    time_l = list(trans_d.keys())
    time_l.sort()
    for t in time_l:
        count_a.append(trans_d[t][0])
        count_c.append(trans_d[t][1])

    return time_l, count_a, count_c

def plot_trans(a, dict_l, day_name, term_name):
    time_l, count_a, count_c = get_time_count_l(dict_l)
    index = len(time_l)
    y_pos = np.arange(index)
    bar_width = 0.5

    rect1 = a.bar(y_pos, count_a, bar_width, color = 'b', label = 'to Allston')
    rect2 = a.bar(y_pos+bar_width, count_c, bar_width, color = 'r', label = 'to Cambridge' )

    #a.set_xticks(y_pos, time_l, rotation='vertical')
    a.set_xticks(y_pos)
    a.set_xticklabels(time_l, rotation='vertical')
    a.set_ylabel('Students crossing Charles')
    a.set_title(day_name + ', ' + term_name)
    a.legend()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python display_trans.py term_string')
        sys.exit(2)

    trans_time_d_l = mnd.unpickle_data('trans_time_d_l.pkl')
    term = sys.argv[1]
    disp_num = 0
    for i in range(0, len(trans_time_d_l)):
        if len(trans_time_d_l[i]) > 0:
            disp_num += 1

    fig, ax = plt.subplots(1,disp_num, figsize = (15,3))
    #fig, ax = plt.subplots(2, 3, figsize = (8,9))

    i = 0
    for d in ct.days:
        ind = d.value
        if len(trans_time_d_l[ind]) > 0:
            a = ax[i]
            plot_trans(a, trans_time_d_l[ind], d.name, term)
            i += 1
    plt.tight_layout()
    plt.savefig('trans_fig.pdf')
    plt.show()




