#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Created on Thursday, Apr 4 2019

@author chong

Builds a dictionary that summarizes conflicts between pairs of
courses. It does so by reading in a multi-year enrollment data file
and building a dictionary keyed by student id of their courses they
have taken in their career. It uses this dictionary to count, for a
given pair of courses, the number of students that have taken both
courses in their career and summarize when in their career they took
them (e.g., same semester, same year, whether one is almost always
taken before the other [and may thus be a prerequisite], etc).

This dictionary forms the basis for identifying pairs of courses that
would be bad (or good) if they conflict in the new schedule.
"""

import warnings
import sys, csv
import make_name_dicts as md
from allston_course_selector import will_be_allston_course_subj_catalog
from collections import defaultdict
from harvard_course_info import cross_list_canonical, is_cross_list_canonical, no_lecture_courses


def canonical_course_name(subject, catalog):
    """
    Put a course name in canonical form (e.g., "ECON 10A")
    """
    return (str(subject).strip() + " " + str(catalog).strip()).upper()

def parse_canonical_course_name(cn):
    start = cn.find(' ')
    subject = cn[:start]
    catalog = cn[start+1:]

    assert subject == subject.upper().strip()
    assert catalog == catalog.upper().strip()
    
    return (subject, catalog)

    
def parse_term(t):
    """
    Break a term string "2018 Fall" into (2018, "Fall")
    """
    start = t.find(' ')
    year = t[:start]
    semester = t[start+1:]

    assert semester in ["Spring", "Fall", "Summer"], "Term was %s"%t
    
    return (int(year), semester)

def term_cmp(t1, t2):
    """
    Compare two terms in chronological order
    """
    (y1, s1) = parse_term(t1)
    (y2, s2) = parse_term(t2)

    if y1 < y2:
        return -1

    if y2 < y1:
        return 1

    # same year
    if s1 == s2:
        return 0
    if s1 == "Spring":
        assert s2 in ["Summer", "Fall"]
        return -1

    if s2 == "Spring":
        assert s1 in ["Summer", "Fall"]
        return 1

    if s1 == "Summer":
        assert s2 in ["Fall"]
        return -1

    if s2 == "Summer":
        assert s1 in ["Fall"]
        return 1
    
    assert False

def term_diff(t1, t2):
    """
    Compute the difference (in number of terms) between t1 and t2. If t1 is before t2 then return a negative number.
    For example, if t1 is "2018 Spring" and t2 is "2018 Fall" then this function will return -1.
    For example, if t1 is "2018 Spring" and t2 is "2019 Spring" then this function will return -2.
    """
    (y1, s1) = parse_term(t1)
    (y2, s2) = parse_term(t2)

    assert s1 in ["Spring", "Fall"]
    assert s2 in ["Spring", "Fall"]

    # Represent the terms as numbers and take the difference
    n1 = y1 * 2
    if s1 == "Fall":
        n1 += 1
        
    n2 = y2 * 2
    if s2 == "Fall":
        n2 += 1

    return n1 - n2
        
def is_summer_term(t):
    """
    Is this a summer term?
    """
    (y1, s1) = parse_term(t)

    if s1 == "Summer":
        return True

    assert s1 in ["Fall", "Spring"]
    
    return False
    
class career(object):
    """
    A class that holds information about a student's career.
    """
    def __init__(self, huid, class_of, concentration):
        self.huid = huid
        self.class_of = class_of
        self.concentration = concentration

        # dictionary from canonical course name to the term in which it was taken
        self.courses_d = {}

    def add_course(self, cn, term):
        assert is_cross_list_canonical(cn), cn
        
        if is_summer_term(term):
            # don't bother recording summer terms
            return
        
        if cn not in self.courses_d:
            self.courses_d[cn] = term
            return
        
        # looks like we've already processed this course
        # check it was in the same term
        if self.courses_d[cn] != term:
            # huh, different terms
            # record the earlier one
            # This is appropriate for courses the student failed and re-took,
            # and for repeatable courses, we don't really care...
            if term_cmp(term, self.courses_d[cn]) < 0:
                self.courses_d[cn] = term



class course_pair_stats(object):
    """
    A class that holds information about a pair of courses and when students took them.
    """
    def __init__(self, cn1, cn2, cn1_in_allston, cn2_in_allston):
        self.cn1 = cn1 
        self.cn2 = cn2 
        assert cn1 < cn2, "%s not less than %s"%(cn1,cn2)

        assert is_cross_list_canonical(cn1)
        assert is_cross_list_canonical(cn2)

        self.cn1_in_allston = cn1_in_allston
        self.cn2_in_allston = cn2_in_allston
        
        # Is at least one of the courses to be in allston?
        self.in_allston = cn1_in_allston or cn2_in_allston
        
        # Number of students that took this pair of courses in their career
        self.num_students = 0

        # Number that took this pair in the same term
        self.num_same_term = 0

        # number that took cn1 before cn2
        self.num_before = 0
        
        # number that took cn1 after cn2
        self.num_after = 0

        # number that took cn1 and cn2 within one term of each other
        self.num_within_one = 0

        # number that took cn1 and cn2 within two terms of each other        
        self.num_within_two = 0
        
        # number that took cn1 and cn2 within three terms of each other        
        self.num_within_three = 0

    def count_student(self, t1, t2):
        """
        Invoked to count a student that took cn1 in term t1 and cn2 in term t2
        """
        self.num_students += 1

        cmp = term_cmp(t1, t2)
        if cmp < 0:
            self.num_before += 1
        elif cmp > 0:
            self.num_after += 1
        elif cmp == 0:
            self.num_same_term += 1

        diff = term_diff(t1, t2)
        if abs(diff) <= 1:
            self.num_within_one += 1

        if abs(diff) <= 2:
            self.num_within_two += 1
            
        if abs(diff) <= 3:
            self.num_within_three += 1
            

class course_stats(object):
    """
    A class that holds information about a courses and when students took them.
    """
    def __init__(self, cn):
        self.cn = cn

        assert is_cross_list_canonical(cn)
        
        # Number of students that took this course (at least once) in their career (in the spring or fall)
        self.num_students = 0

        # Number of students that took this course (the first time) in the fall
        self.num_fall = 0

        # Number of students that took this course (the first time) in the srping
        self.num_spring = 0

        # Dictionary from term to enrollment count
        self.term_enrollment = defaultdict(int)

    def count_student(self, term):
        """
        Invoked to count a student that took this sould in the given term
        """
        self.num_students += 1
        (year, semester) = parse_term(term)

        assert semester in ["Fall", "Spring"]
        
        if semester == "Fall":
            self.num_fall += 1
            
        if semester == "Spring":
            self.num_spring += 1

        self.term_enrollment[term] += 1

    @property
    def is_large(self):
        # Course is large if it had more than 100 students in at least 2 terms
        # Also have some hard coded exceptions
        if self.cn in ['COMPSCI 20', 'COMPSCI 109A', 'COMPSCI 109B', 'APPHY 50A', 'APPHY 50B', 'ECON 1017', 'ECON 1420', 'GOV 1280', 'GOV 1790']:
            return True

        if self.cn in no_lecture_courses:
            return False
        
        return len([True for enr in self.term_enrollment.values() if enr >= 100]) > 1
        
def build_career_sched(csv_in, colindex):
    """
    Build (1) a dictionary keyed by student id with value a student career schedule that reflects courses the
    student has taken over their career, and (2) a dictionary keyed by pairs of courses that summarize how many
    students took that pair of courses, and info about how they took that pair of courses.

    :param csv_in: A csv file of the format supplied by the registrar for all of the courses over multiple years
    :return: ???
    """
    st_sched_d = {}
    count = 0
    for l in csv_in:
        count = count+1
        huid = l[colindex["HUID"]]
        concentration = l[colindex["CONCENTRATION"]]
        term = l[colindex["TERM"]]
        subject = l[colindex["SUBJECT"]]
        catalog = l[colindex["CATALOG"]]

        if "CLASS_OF" in colindex:
            class_of = l[colindex["CLASS_OF"]]
        else:
            class_of = None

        if huid not in st_sched_d:
            # student is not yet in the dictionary.
            st_sched_d[huid] = career(huid, class_of, concentration)

        car = st_sched_d[huid]

        
        cn = canonical_course_name(subject, catalog)
        cn = cross_list_canonical(cn)
        car.add_course(cn, term)

    print("Total enrollment entries: ",count)
    return st_sched_d


def build_course_pair_stats_d(st_sched_d):
    course_stats_d = {}
    course_pair_stats_d = {}
    # For each student, go through their career courses and record information about each pair
    for huid, car in st_sched_d.items():
        clist = list(car.courses_d.keys())
        for i in range(len(clist)):
            (cn_i, t_i) = (clist[i], car.courses_d[clist[i]])

            if cn_i not in course_stats_d:
                course_stats_d[cn_i] = course_stats(cn_i)
            
            course_stats_d[cn_i].count_student(t_i)
            
            for j in range(i+1, len(clist)):
                (cn_j, t_j) = (clist[j], car.courses_d[clist[j]])

                
                cp = (cn_i, cn_j) if cn_i < cn_j else (cn_j, cn_i)
                tp = (t_i, t_j) if cn_i < cn_j else (t_j, t_i)

                if cp not in course_pair_stats_d:
                    (subj1, cat1) = parse_canonical_course_name(cp[0])
                    (subj2, cat2) = parse_canonical_course_name(cp[1])
                    cn1_in_allston = will_be_allston_course_subj_catalog(subj1, cat1)
                    cn2_in_allston = will_be_allston_course_subj_catalog(subj2, cat2)
                    in_allston = cn1_in_allston or cn2_in_allston
                    course_pair_stats_d[cp] = course_pair_stats(cp[0], cp[1], cn1_in_allston, cn2_in_allston)

                stats = course_pair_stats_d[cp]
                stats.count_student(tp[0], tp[1])

    return (course_pair_stats_d, course_stats_d)


def build_column_index(headers, required_cols, optional_cols):
    """
    Given a list of headers from the data set,
    and a list of required column names (required_cols) and a list of optional column names (optional_cols),
    returns a dictionary from the elements of desired_cols and optional_cols to the index of headers.
    This utility method is useful to give a little robustness to CSV data files, where the data file
    might have columns reordered, etc.
    """
    index_d = {}

    def canon(s):
        """
        Remove spaces, underscores, etc.
        """
        return s.lower().replace(" ", "").replace("_","")

    # Canoncize headers, including removing any Unicode BOM bytes.
    hd = [ canon(s.replace(u'\ufeff','')) for s in headers ]
    
    for n in required_cols:
        cn = canon(n)
        assert cn in hd, "Expected to find column name %s in CSV file, but only had %s"%(n,headers)
        index_d[n] = hd.index(cn)

    for n in optional_cols:
        cn = canon(n)
        if cn in hd:
            index_d[n] = hd.index(cn)

    return index_d


if __name__ == '__main__':

    def usage():
        print('Usage: build_course_pair_stats_d <multi-year-enrollments.csv>')
        sys.exit(1)
        
    if len(sys.argv) != 2:
        usage()


    def brief_warning(message, category, filename, lineno, line=None):
        return "Warning: %s\n"%message

    warnings.formatwarning = brief_warning


    filename = sys.argv[1]

    fin = open(filename, 'r')
    cin = csv.reader(fin)

    # discard first row (which contains headers)
    headers = next(cin)
    colindex = build_column_index(headers, ["HUID","TERM","SUBJECT","CATALOG", "CONCENTRATION"], ["CLASS_OF"])

    st_sched_d = build_career_sched(cin, colindex)

    fin.close()
    
    res = build_course_pair_stats_d(st_sched_d)

    outfilename = 'course_pair_stats_d.pkl'
    print('Writing file %s'%outfilename)
    md.pickle_data(outfilename, res)

    
