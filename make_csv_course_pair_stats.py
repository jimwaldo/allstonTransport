#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-04-04

@author chong

Using course_pair_stats_d.pkl, created by build_course_pair_stats_d.py, produce a csv file
listing pairs of courses and statistics about how many students take them.
"""
import pickle, csv, sys

import make_name_dicts as md
import operator as op
from build_course_pair_stats_d import course_pair_stats, course_stats, parse_canonical_course_name

def write_course_pair_stats_csv(course_pair_stats_d, course_stats_d, csv_out):
    header_l =[ 'Course1', 'Course2',
                'Course1_students', 'Prop_course_1_fall', 'Prop_course_1_spring',
                'Course2_students', 'Prop_course_2_fall', 'Prop_course_2_spring',
                'in_allston',
                'allways_diff_semesters',
                'Num_students',
                'Prop_Course1_students', 'Prop_Course2_students',
                'Num_same_term', 'Prop_same_term',
                'Num_before', 'Prop_before',
                'Num_after', 'Prop_after',
                'Num_within_one_semester', 'Prop_within_one_semester',
                'Num_within_two_semesters', 'Prop_within_two_semesters',
                'Num_within_three_semesters', 'Prop_within_three_semesters',
                'Candidate_bad_conflict'
    ]
    csv_out.writerow(header_l)

    count = 0
    count_candidate = 0
    
    for (cn1, cn2), stats in course_pair_stats_d.items():
        n = stats.num_students
        if n > 40 and stats.in_allston:            
            count += 1

            cn1num = course_stats_d[cn1].num_students
            cn2num = course_stats_d[cn2].num_students

            prop_cn1_fall = course_stats_d[cn1].num_fall/cn1num
            prop_cn1_spring = course_stats_d[cn1].num_spring/cn1num
            prop_cn2_fall = course_stats_d[cn2].num_fall/cn2num
            prop_cn2_spring = course_stats_d[cn2].num_spring/cn2num

            always_diff_semester = (prop_cn1_fall >= 0.99 and prop_cn2_spring >= 0.99) \
                                   or (prop_cn2_fall >= 0.99 and prop_cn1_spring >= 0.99)
            
            prop_same_term = stats.num_same_term/n
            prop_before = stats.num_before/n
            prop_after = stats.num_after/n
            prop_within_one = stats.num_within_one/n
            prop_within_two = stats.num_within_two/n
            prop_within_three = stats.num_within_three/n

            (subj1, cat1) = parse_canonical_course_name(cn1)
            (subj2, cat2) = parse_canonical_course_name(cn2)
            
            def is_candidate_bad_conflict():
                lots_of_sections = ["EXPOS 20", "MATH 1A", "MATH 1B", "MATH 21A", "MATH 21B"]
                if cn1 in lots_of_sections or cn2 in lots_of_sections:
                    # one of the courses has lots of sections                    
                    return False
                
                no_lectures = ["ENG-SCI 100HFB", "ENG-SCI 91R", "COMPSCI 91R" ]
                if cn1 in no_lectures or cn2 in no_lectures:
                    # Has no lecture
                    return False
                
                if subj1 in ['SOCWORLD', 'CULTBLF', 'US-WORLD', 'ETHRSON', 'SCILIVSY', 'SCIPHUNV', 'AESTHINT', 'INDSTUDY']:
                    # Ignore Gen Eds
                    return False
                if subj2 in ['SOCWORLD', 'CULTBLF', 'US-WORLD', 'ETHRSON', 'SCILIVSY', 'SCIPHUNV', 'AESTHINT', 'INDSTUDY']:
                    # Ignore Gen Eds
                    return False
                
                # ignore them if they are in different semesters
                if always_diff_semester:
                    return False
                
                if prop_same_term >= 0.4:
                    return True
                if prop_within_three >= 0.7 and prop_before >= 0.13 and prop_after >= 0.13:
                    return True


            if is_candidate_bad_conflict():
                count_candidate += 1
                
            csv_out.writerow([cn1, cn2,
                              str(cn1num), "{:.2f}".format(prop_cn1_fall), "{:.2f}".format(prop_cn1_spring),
                              str(cn2num), "{:.2f}".format(prop_cn2_fall), "{:.2f}".format(prop_cn2_spring),
                              stats.in_allston,
                              "TRUE" if always_diff_semester else "FALSE",
                              str(n),
                              "{:.2f}".format(n/cn1num), "{:.2f}".format(n/cn2num),
                              str(stats.num_same_term), "{:.2f}".format(prop_same_term),
                              str(stats.num_before), "{:.2f}".format(prop_before),
                              str(stats.num_after), "{:.2f}".format(prop_after),
                              str(stats.num_within_one), "{:.2f}".format(prop_within_one),
                              str(stats.num_within_two), "{:.2f}".format(prop_within_two),
                              str(stats.num_within_three), "{:.2f}".format(prop_within_three),
                              "TRUE" if is_candidate_bad_conflict() else "FALSE"
            ])

    print("%s course pairs output, %s candidates for bad conflicts"%(count, count_candidate))

if __name__ == '__main__':
    def usage():
        print('Usage: python make_csv_course_pair_stats.py out_file.csv')
        sys.exit(1)

    if len(sys.argv) != 2:
        usage()

    out_file = open(sys.argv[1], 'w')


    (course_pair_stats_d, course_stats_d) = md.unpickle_data('course_pair_stats_d.pkl')
    c_out = csv.writer(out_file)
    write_course_pair_stats_csv(course_pair_stats_d, course_stats_d, c_out)
        
    out_file.close()
