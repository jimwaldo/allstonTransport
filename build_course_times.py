#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 2018

@author: waldo

Build a dictionary keyed by class number with values course time objects, which contain the class number, the start
and end time, an indicator of where the class is taught (Cambridge or Allston), and a list indicating the days of the
week that the course meets. The courses for which the dictionary is built is determined by the set of classes read
from a pkl file generated by an earlier program; also used is the set of classes that are taught in
Allston, which resides in another generated file. If a class is not in this set, it is assumed to be taught in
Cambridge. The program also uses a csv file provided by the registrar containing all of the course time information, this
must be named course_time.csv and reside in the directory in which the program is run.
"""
import csv, sys
import make_name_dicts as mnd
import class_time as ct
import allston_course_selector as acs
import warnings

def build_ct_d(csv_in, convert_to_allston):
    """
    Build a dictionary indexed by course_num with values course_time objects that will indicate the start time,
    end time, and days of the week for each course, along with where the course is taught.
    :param csv_in: A csv file in the format of the course_time.csv supplied by the registrar
    :param convert_to_allston: boolean indicating whether we should convert course times for courses indicated as being in Allston.
    :return: a dictionary indexed by course_num with values course_time objects
    """
    ret_d = {}
    for l in csv_in:
        in_allston = acs.will_be_allston_course(l)

        cto = ct.course_time(l, in_allston)
        course_name=(l[3] + l[4])
        
        # if the course is meant to be in Allston, then update it.
        if in_allston and convert_to_allston:
            cto.convert_to_allston(course_name=course_name)

        # Check compliant times
        if not cto.is_compliant_time():
            warnings.warn("Course " +course_name + " in " + ("Cambridge" if cto.where == 'c' else "Allston") + " is not at a compliant time: it starts at " + cto.time_start)
            
        
        ret_d[l[1]] = cto
        #print (course_name+",:\t"+ str(cto))
        
    return ret_d

if __name__ == '__main__':

    def usage():
        print('Usage: python [--convert-to-allston] <courses_times.csv>')
        sys.exit(1)
        
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()


    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning


    filename = sys.argv[1]
    convert_to_allston = False

    if sys.argv[1].startswith("--"):
        if sys.argv[1] == "--convert-to-allston":
            convert_to_allston = True
            if len(sys.argv) == 2:
                usage()
            filename = sys.argv[2]
        else:
            usage()

    fin = open(filename, 'r')
    cin = csv.reader(fin)
    h = next(cin)

    class_time_d = build_ct_d(cin, convert_to_allston)

    fin.close()
    mnd.pickle_data('class_time_d.pkl', class_time_d)