#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 12 10:18:18 2018

@author: waldo

A set of utility routines that make live easier in the rest of the project.
"""

import pickle, csv

def build_faculty_dict(fin):
    '''
    build a pair of dictionaries that allow mapping from faculty name to faculty huid. This was useful when we thought
    we would determine what classes were taught in Allston by who was teaching them. This turned out to be too hard
    given the data that we got from the registrar.
    :param fin: a csv.reader of a file mapping faculty names to faculty huids
    :return: a pair of dictionaries, mapping from huids to names and from names to huids
    '''
    huid_dict = {}
    name_dict = {}
    for l in fin:
        huid_dict[l[0]] = l[2] + ' ' + l[1]
        name_dict[l[2] + ' ' + l[1]] = l[0]
    return huid_dict, name_dict
        
        
def build_student_class_dict(fin):
    '''
    Build a pair of dictionaries mapping from students to the classes and terms of the courses they took, and from
    the term and classes to the students in that class. Not needed after deciding to move to treating the different
    terms separately.
    :param fin: The enrollment file, as a csv.reader, containing all of the classes for all of the terms
    :return: a pair of dictionaries, mapping class+term to students in the class and students to the classes/terms
    '''
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
    @param f_name : name of the file to create to store the pickled data structure. If the file already exists, the
    existing file will be overwritten
    @param to_pickle: the data structure to be pickled in the named file.
    :return: None
    '''
    p_out = open(f_name, 'wb')
    pickle.dump(to_pickle, p_out)
    p_out.close()
    return

def unpickle_data(fname):
    '''
    Unpickle the data structure stored in the named file, and return that structure. Note that the routine does no
    error checking; if the file doesn't exist, or doesn't contain a pickle, or the structure pickled has structure that
    hasn't been imported into the program, the routine will fail.
    :param fname: The name of the file that contains a pickle of the data structure to be returned
    :return: the structure saved in the named file
    '''
    p_in = open(fname, 'rb')
    ret_val = pickle.load(p_in)
    p_in.close()
    return ret_val

def get_filtered_set(record_set,from_filter, comp_index, target_index):
    '''
    Create a set of values from a csv.reader, filtered by the line in question having an indexed value that is in
    the set passed in. Returns the set of values of the index supplied.
    :param record_set: A csv.reader that will be filtered
    :param from_filter: A set that will determine whether to add a value to the returned set; if the comp_index is in the
    set, the value of the target index will be added to the return set
    :param comp_index: Index of the value to be checked; if the value is in from_filter then the value in position
    target_index will be added to the return set
    :param target_index: The index of the value to be added to the returned set if the comp_index value is in the set
    from_filter
    :return: the set of values from target_index that were in lines where the value of comp_index was in from_filter
    '''
    return_set = set()
    for l in record_set:
        if len(l) < (comp_index + 1):
            continue
        if l[comp_index]in from_filter:
            return_set.add(l[target_index])
    return return_set

def get_subjects(fname_in):
    '''
    Build a set of subjects from the file named by fname_in. The file is assumed to be a .csv file of the form of the
    form in enrollment.csv. The set of subjects will be written to a csv, along with a column that allows a user to
    fill in whether or not the subject will be taught in Allston.
    :param fname_in: The name of a .csv file in the form of enrollment.csv
    :return: A set of the Subject values in the file.
    '''
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
    
def build_class_set(sub_set, class_set, enroll_in):
    for l in enroll_in:
        if l[3] in sub_set:
            class_num = l[3] + ' ' + l[4]
            class_set.add(class_num)
        
    return class_set

    