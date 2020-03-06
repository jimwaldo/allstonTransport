#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2019-04-04

@author chong

Using course_pair_stats_d.pkl, created by build_course_pair_stats_d.py, produce a csv file
listing large courses.
"""
import pickle, csv, sys

import make_name_dicts as md
import operator as op
from build_course_pair_stats_d import course_pair_stats, course_stats, parse_canonical_course_name, term_cmp
from allston_course_selector import will_be_allston_course_canonical_cn
from harvard_course_info import is_cross_list_canonical


from functools import cmp_to_key

def write_large_courses_csv(course_pair_stats_d, course_stats_d, csv_out):
    # Get the list of terms.
    term_keys = set()
    for cn, stats in course_stats_d.items():
        term_keys.update(stats.term_enrollment.keys())

    # sort the list of terms
    term_keys = list(term_keys)
    term_keys.sort(key=cmp_to_key(term_cmp), reverse=True)


    header_l =[ 'Course' , 'Allston' ] + term_keys
    csv_out.writerow(header_l)

    count = 0
    for cn, stats in sorted(course_stats_d.items()):
        assert is_cross_list_canonical(cn)
        
        if stats.is_large:
            vals = [cn, "True" if will_be_allston_course_canonical_cn(cn) else "False"]
            vals += [stats.term_enrollment[tk] for tk in term_keys]
            csv_out.writerow( vals )
            count += 1

    print("%s large courses"%(count))

if __name__ == '__main__':
    def usage():
        print('Usage: python make_csv_large_courses.py out_file.csv')
        sys.exit(1)

    if len(sys.argv) != 2:
        usage()

    out_file = open(sys.argv[1], 'w')


    (course_pair_stats_d, course_stats_d) = md.unpickle_data('course_pair_stats_d.pkl')
    c_out = csv.writer(out_file)
    write_large_courses_csv(course_pair_stats_d, course_stats_d, c_out)
        
    out_file.close()
