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
from collections import OrderedDict
from build_course_pair_stats_d import course_pair_stats, course_stats, parse_canonical_course_name
import scheduling_course_time as sct
from harvard_course_info import no_lecture_courses

def write_course_pair_stats_csv(course_pair_stats_d, course_stats_d, schedules, csv_out):
    header_l =[ 'Course1', 'Course2',
                'Weighted_conflict_score',
                'Course1_students', 'Prop_course_1_fall', 'Prop_course_1_spring',
                'Course2_students', 'Prop_course_2_fall', 'Prop_course_2_spring',
                'in_allston',
                'always_diff_semesters',
                'Num_students',
                'Prop_Course1_students', 'Prop_Course2_students',
                'Num_same_term', 'Prop_same_term',
                'Num_before', 'Prop_before',
                'Num_after', 'Prop_after',
                'Num_within_one_semester', 'Prop_within_one_semester',
                'Num_within_two_semesters', 'Prop_within_two_semesters',
                'Num_within_three_semesters', 'Prop_within_three_semesters',
                'Course1_is_large','Course2_is_large','either_large',
                'Candidate_bad_conflict'
    ]

    for term in schedules:
        header_l += ['conflict %s'%term]
    
    csv_out.writerow(header_l)

    count = 0
    count_candidate = 0

    printAll = False
    for (cn1, cn2), stats in course_pair_stats_d.items():
        n = stats.num_students
        cn1num = course_stats_d[cn1].num_students
        cn2num = course_stats_d[cn2].num_students

        grad = False

        show_if_above = 100
        show_if_prop_high = 50

        if grad:
            show_if_above = 50
            show_if_prop_high = 20
            
        if n > 100 or (n > 50 and (n/cn1num > 0.5 or n/cn2num > 0.5)): # printAll or (n > 40 and stats.in_allston):
            count += 1


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

            def bad_conflict_score():
                if cn1 in no_lecture_courses or cn2 in no_lecture_courses:
                    # Has no lecture
                    return 0.0
                
                if subj1 in ['SOCWORLD', 'CULTBLF', 'US-WORLD', 'ETHRSON', 'SCILIVSY', 'SCIPHUNV', 'AESTHINT', 'INDSTUDY']:
                    # Ignore Gen Eds
                    return 0.0
                if subj2 in ['SOCWORLD', 'CULTBLF', 'US-WORLD', 'ETHRSON', 'SCILIVSY', 'SCIPHUNV', 'AESTHINT', 'INDSTUDY']:
                    # Ignore Gen Eds
                    return 0.0
                
                # ignore them if they are in different semesters
                if always_diff_semester:
                    return 0.0
                
                if prop_same_term >= 0.4:
                    return 1.0
                if prop_within_three >= 0.7 and prop_before >= 0.13 and prop_after >= 0.13:
                    return 1.0

                # Use a sliding scale for the rest...
                score1 = prop_same_term / 0.4
                score2 = min(prop_within_three / 0.7, 1.0) * min(prop_before / 0.13, 1.0) * min(prop_after / 0.13, 1.0)
                assert score1 >= 0.0 and score1 <= 1.0
                assert score2 >= 0.0 and score2 <= 1.0
                return max(score1, score2)



            # A weighted score on how much we should try to avoid this conflict
            bc_score = bad_conflict_score()
            weighted_score = bc_score * stats.num_within_two
            is_candidate_bad_conflict = bc_score >= 1.0
            
            if is_candidate_bad_conflict:
                count_candidate += 1

            conflicts = []
            for term in schedules:
                sched = schedules[term]
                confl = "FALSE"
                if cn1 in sched and cn2 in sched:
                    if sct.courses_conflict(sched[cn1], sched[cn2]):
                        confl = "TRUE"

                conflicts.append(confl)

            
            csv_out.writerow([cn1, cn2,
                              str(int(weighted_score)),
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
                              "TRUE" if course_stats_d[cn1].is_large else "FALSE",
                              "TRUE" if course_stats_d[cn2].is_large else "FALSE",
                              "TRUE" if (course_stats_d[cn1].is_large or course_stats_d[cn2].is_large) else "FALSE",
                              "TRUE" if is_candidate_bad_conflict else "FALSE"]
                             + conflicts)

    print("%s course pairs output, %s candidates for bad conflicts"%(count, count_candidate))

if __name__ == '__main__':
    def usage():
        print('Usage: python make_csv_course_pair_stats.py out_file.csv [-schedule "Term name" schedule.csv]*')
        print('  Zero or more schedule options can be passed, which will be used')
        print('  to indicate whether the course pairs conflict in that term.')
        print('  For example -schedule "Fall 2019" course_times_2019_fall.csv -schedule "Spring 2020" course_times_2020_spring.csv')
        sys.exit(1)

    if len(sys.argv) < 2:
        usage()

    outfilename = sys.argv[1]    
    # try to parse outputs
    ind = 2
    schedules = OrderedDict()
    while True:
        if len(sys.argv) == ind:
            # we are at the end
            break

        if len(sys.argv) < ind+2:
            usage()

        if sys.argv[ind] not in ['-schedule', '-sched']:
            usage()

        
        term_name = sys.argv[ind+1]
        sched_filename = sys.argv[ind+2]
        ind += 3

        # open the file
        fschedin = open(sched_filename, 'r')
        cschedin = csv.reader(fschedin)
        sched_d = sct.build_course_schedule(cschedin,filename=sched_filename)
        fschedin.close()
        schedules[term_name] = sched_d
        
    out_file = open(outfilename, 'w')


    (course_pair_stats_d, course_stats_d) = md.unpickle_data('course_pair_stats_d.pkl')
    c_out = csv.writer(out_file)
    write_course_pair_stats_csv(course_pair_stats_d, course_stats_d, schedules, c_out)
        
    out_file.close()
