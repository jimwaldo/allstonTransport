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
    count_l = []

    time_l = list(trans_d.keys())
    time_l.sort()
    for t in time_l:
        count_l.append(trans_d[t])
    return time_l, count_l

def plot_trans(a, dict_l, day_name, term_name):
    time_l, count_l = get_time_count_l(dict_l)
    y_pos = np.arange(len(time_l))

    a.bar(time_l, count_l, align='center', alpha = 0.5)
#    a.set_xticks(y_pos, time_l, rotation='vertical')
    a.set_xticks(y_pos)
    a.set_xticklabels(time_l, rotation='vertical')
    a.set_ylabel('Students crossing Charles')
    a.set_title(day_name + ', ' + term_name)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python display_trans.py trans_time_d_l.pkl term_string')
        sys.exit(2)

    trans_time_d_l = mnd.unpickle_data(sys.argv[1])
    term = sys.argv[2]
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




