#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Monday March 18, 2019

@author chong

Run all of the analyses on data files. Must be given the course_times.csv and enrollments.csv files.

It assumes that all python files are in the same directory as this file, and will create all data files in the
same directory as the course_times.csv file.
"""
import os
import sys

def run_command(cmd_dir, cmd, args):
    args_str = " ".join(args)
    print ('\n' + ('-' * 50))
    print ('|')
    print ('|  Running "%s %s"'%(cmd, args_str))
    print ('|')
    ret = os.system("%s%s%s %s"%(cmd_dir,os.sep,cmd, args_str))

    if ret != 0:
        raise Exception()

if __name__ == '__main__':

    def usage():
        print('Usage: python do_all_analyses.py [--convert-to-allston] course_times.csv enrollments.csv')
        print('   All files will be created in the same directory as the course_times.csv file.')
        sys.exit(2)


    if len(sys.argv) < 3 or len(sys.argv) > 4:
        usage()

    convert_to_allston = False
    course_times_file = sys.argv[1]
    enrollments_file = sys.argv[2]

    if sys.argv[1].startswith("-"):
        if sys.argv[1] == "--convert-to-allston":
            convert_to_allston = True
            course_times_file = sys.argv[2]
            enrollments_file = sys.argv[3]
        else:
            usage()
        

    if enrollments_file.find("course") >= 0:
        # probably a mistake
        usage()


    if not os.path.isfile(course_times_file):
        print("Can't find file %s"%course_times_file)
        usage()

    if not os.path.isfile(enrollments_file):
        print("Can't find file %s"%enrollments_file)
        usage()
        
    cmd_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.dirname(os.path.realpath(course_times_file))
    orig_wd = os.getcwd()

    course_times_filename = os.path.basename(course_times_file)
    if os.path.dirname(os.path.realpath(enrollments_file)) == data_dir:
        # enrollments file is in the same directory as course times!
        enrollments_filename = os.path.basename(enrollments_file)
    else:
        enrollments_filename = os.path.realpath(enrollments_file)
        
    print ("Command directory  : %s"%cmd_dir)
    print ("Data file directory: %s"%data_dir)

    print ("Changing working directory to data file directory...")
    os.chdir(data_dir)

    # Check that we can still find the data fiales
    if not os.path.isfile(course_times_filename):
        print("Can't find file %s after changing directory!"%course_times_filename)
        exit(2)

    if not os.path.isfile(enrollments_filename):
        print("Can't find file %s after changing directory!"%enrollments_filename)
        exit(2)
    
    
    # Now run all the analyses!

    try:
        run_command(cmd_dir,"split_classes_students.py", [enrollments_filename])

        if convert_to_allston:
            run_command(cmd_dir,"build_course_times.py", ["--convert-to-allston", course_times_filename])
        else:
            run_command(cmd_dir,"build_course_times.py", [course_times_filename])


        run_command(cmd_dir,"build_student_schedule.py", [])
        run_command(cmd_dir,"build_transition_d.py", [])
        run_command(cmd_dir,"build_transition_time_d.py", [])
        run_command(cmd_dir,"make_csv_transitions.py", ["transitions.csv"])

        run_command(cmd_dir,"build_conflicts_d.py", [])
        run_command(cmd_dir,"make_csv_conflicts.py", [course_times_filename, "conflicts.csv"])

        run_command(cmd_dir,"build_no_lunch_d.py", [])    

        # Alpha: put in call to create a suitable presentation of data?
        
    except:
        print ("\n\nError encountered, skipping remaining analyses...")
        
    print ("\n\nRestoring original working directory...")
    os.chdir(orig_wd)
    