#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 10:18:18 2018

@author: waldo
"""

import pickle, csv

def build_faculty_dict(fin):
    huid_dict = {}
    name_dict = {}
    for l in fin:
        huid_dict[l[0]] = l[2] + ' ' + l[1]
        name_dict[l[2] + ' ' + l[1]] = l[0]
    return huid_dict, name_dict
        
        
def build_student_class_dict(fin):
    student_class_dict = {}
    class_student_dict = {}
    
    for l in fin:
        if len(l) < 9:
            continue
        class_term = [l[0], l[2]]
        student_class_dict.setdefault(l[8], []).append([l[3], l[0]])
        class_student_dict.setdefault(l[8], []).append(class_term)
    
    return student_class_dict, class_student_dict

def pickle_data(f_name, to_pickle):
    '''
    Create a file with the supplied name, and pickle the data structure passed
    in to that file.
    
    '''
    p_out = open(f_name, 'wb')
    pickle.dump(to_pickle, p_out)
    p_out.close()
    return

def get_filtered_set(record_set,from_filter, comp_index, target_index):
    return_set = set()
    for l in record_set:
        if len(l) < (comp_index + 1):
            continue
        if l[comp_index]in from_filter:
            return_set.add(l[target_index])
    return return_set

def get_subjects(fname_in):
    fin = open(fname_in, 'r')
    cin = csv.reader(fin)
    h = next(cin)
    
    subject_s = set()
    for l in cin:
        subject_s.add(l[3])
        
    subject_l = list(subject_s)
    pickle_data('subject_set.pkl', subject_s)
    fout = open('subjects.csv', 'w')
    cout = csv.writer(fout)
    cout.writerow(['Subject', 'In Allston'])
    for l in subject_l:
        cout.writerow([l, ''])
        
    fout.close()
    fin.close()
    