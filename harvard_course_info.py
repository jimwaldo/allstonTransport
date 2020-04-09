#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on March 6 2020

@author chong

Code and data to handle specifics of Harvard courses
"""


# #########################
#
# Special lists of courses


# Courses with no lectures. We won't report conflicts with these, or even regard them as "large courses"
no_lecture_courses = ["EXPOS 20", "MATH 1A", "MATH 1B", "MATH 21A", "MATH 21B", "ECON 970", "EXPOS 10", "EXPOS 40",
                      "ENG-SCI 100HFB", "ENG-SCI 91R", "COMPSCI 91R" ]

# #########################
#
# Non-FAS instructor

# Non-FAS instructors can teach on Tuesdays 3-5pm
non_FAS_instructor = ['COMPSCI 109A', 'COMPSCI 109B']

# #########################
#
# Cross listed courses

# This list is the cross-listed courses.
# Each element is a list of cross listed courses, where the first course in the list is the "canonical" course

cross_listed_courses = [
   ['AFRAMER 124Y', 'SPANSH 123'],
   ['AFRAMER 132Z', 'HAA 176E'],
   ['AFRAMER 175X', 'ANTHRO 1750'],
   ['AFRAMER 199X', 'HIST 1937'],
   ['AFRAMER 208', 'ANTHRO 2800'],
   ['AFRAMER 262', 'ANTHRO 2626'],
   ['AFRAMER 305', 'ANTHRO 2800'],
   ['AFVS 158AR', 'ANTHRO 1836AR'],
   ['AFVS 158BR', 'ANTHRO 1836BR', 'VES 158BR'],
   ['AFVS 188G', 'GERMAN 153'],
   ['AFVS 289', 'GERMAN 254'],
   ['AFVS 73', 'ANTHRO 1645'],
   ['AMSTDIES 201', 'HIST 1917'],
   ['AMSTDIES 271', 'MUSIC 298'],
   ['ANTHRO 1059', 'HIST 1059'],
   ['ANTHRO 1080', 'EMR 126'],
   ['ANTHRO 1235', 'HEB 1235'],
   ['ANTHRO 1661', 'HSEMR-LE 75'],
   ['ANTHRO 1761', 'VES 176W'],
   ['ANTHRO 1923', 'HIST 1923'],
   ['ANTHRO 2059', 'HIST 2059'],
   ['ANTHRO 2173', 'SUMERIAN 217'],
   ['ANTHRO 2722', 'VES 252'],
   ['ANTHRO 2725', 'HIST 2725'],
   ['ANTHRO 3555', 'VES 355R'],
   ['COMPSCI 109A', 'APCOMP 209A', 'STAT 121A'],
   ['COMPSCI 109B', 'APCOMP 209B', 'STAT 121B'],
   ['APCOMP 227', 'APMTH 227'],
   ['APCOMP 275', 'APPHY 275'],
   ['APMTH 111', 'ENG-SCI 111'],
   ['APMTH 115', 'ENG-SCI 115'],
   ['APMTH 121', 'ENG-SCI 121'],
   ['APMTH 158', 'ENG-SCI 158'],
   ['APMTH 231', 'ENG-SCI 201'],
   ['APMTH 232', 'ENG-SCI 202'],
   ['APMTH 254', 'ENG-SCI 254'],
   ['APPHY 195', 'PHYSICS 195'],
   ['APPHY 202', 'E-PSCI 202'],
   ['APPHY 284', 'PHYSICS 262'],
   ['APPHY 295A', 'PHYSICS 295A'],
   ['APPHY 295B', 'PHYSICS 295B'],
   ['APPHY 296', 'PHYSICS 296'],
   ['ARAMAIC A', 'RELIGION A'],
   ['ARAMAIC B', 'RELIGION B'],
   ['BCMP 230', 'SCRB 230'],
   ['BE 121', 'ENG-SCI 222'],
   ['BE 125', 'ENG-SCI 230'],
   ['BE 129', 'ENG-SCI 258'],
   ['BE 130', 'ENG-SCI 249'],
   ['BIOSTAT 282', 'STAT 115', 'STAT 215'],
   ['CLASPHIL 212', 'PHIL 208A'],
   ['CLASPHIL 259', 'MEDLATIN 259'],
   ['CLS-STDY 145', 'MODGRK 145'],
   ['CLS-STDY 151', 'MODGRK 146'],
   ['CLS-STDY 167', 'MODGRK 167'],
   ['COMPLIT 106', 'YIDDISH 115'],
   ['COMPLIT 107', 'YIDDISH 107'],
   ['COMPLIT 122', 'SLAVIC 184'],
   ['COMPLIT 137', 'HEBREW 137'],
   ['COMPLIT 143', 'HEBREW 131'],
   ['COMPLIT 151', 'SLAVIC 112'],
   ['COMPLIT 153', 'SLAVIC 154'],
   ['COMPLIT 166', 'YIDDISH 166'],
   ['COMPLIT 167', 'HEBREW 167'],
   ['COMPLIT 173', 'GERMAN 173', 'MUSIC 175R'],
   ['COMPLIT 174', 'GERMAN 174'],
   ['COMPLIT 179', 'JEWISHST 179'],
   ['COMPLIT 180', 'GERMAN 180'],
   ['COMPLIT 188', 'ROM-STD 168'],
   ['COMPLIT 194', 'ENGLISH 194'],
   ['COMPLIT 201', 'GERMAN 291', 'ROM-STD 201'],
   ['COMPLIT 204', 'ENGLISH 292PH'],
   ['COMPLIT 212', 'GERMAN 287'],
   ['COMPLIT 217', 'ROM-STD 217'],
   ['COMPLIT 228', 'ENGLISH 256CR'],
   ['COMPLIT 242', 'GERMAN 242'],
   ['COMPSCI 10', 'STAT 10'],
   ['COMPSCI 127', 'COMPSCI 227R', 'COMPSCI 227'],
   ['COMPSCI 144R', 'COMPSCI 244R'],
   ['COMPSCI 145', 'COMPSCI 245'],
   ['COMPSCI 146', 'COMPSCI 246'],
   ['COMPSCI 148', 'COMPSCI 248'],
   ['COMPSCI 282R', 'STAT 317'],
   ['E-PSCI 56', 'OEB 56'],
   ['E-PSCI 101', 'ESE 101'],
   ['E-PSCI 107', 'OEB 107'],
   ['E-PSCI 109', 'ENG-SCI 109', 'ESE 109'],
   ['E-PSCI 112', 'ENG-SCI 112'],
   ['E-PSCI 122', 'ESE 122'],
   ['E-PSCI 129', 'ESE 129'],
   ['E-PSCI 130', 'ENG-SCI 130'],
   ['E-PSCI 131', 'ENG-SCI 131', 'ESE 131'],
   ['E-PSCI 132', 'ESE 132'],
   ['E-PSCI 133', 'ENG-SCI 133', 'ESE 133'],
   ['E-PSCI 135', 'ENG-SCI 135'],
   ['E-PSCI 138', 'ESE 138'],
   ['E-PSCI 139', 'E-PSCI 230'],
   ['E-PSCI 141', 'E-PSCI 240'],
   ['E-PSCI 145', 'E-PSCI 245'],
   ['E-PSCI 146', 'E-PSCI 247'],
   ['E-PSCI 160', 'ENG-SCI 160', 'ESE 160'],
   ['E-PSCI 162', 'ENG-SCI 162', 'ESE 162'],
   ['E-PSCI 187', 'E-PSCI 287'],
   ['E-PSCI 237', 'ENG-SCI 237'],
   ['E-PSCI 274', 'E-PSCI 174'],
   ['EMR 123', 'RELIGION 1590'],
   ['EMR 131', 'WOMGEN 1283'],
   ['EMR 133', 'WOMGEN 1204'],
   ['EMR 139', 'RELIGION 2519'],
   ['ENG-SCI 100HFA', 'ENG-SCI 100HFB'],
   ['ENG-SCI 128', 'ENG-SCI 228'],
   ['ENG-SCI 139', 'ENG-SCI 239'],
   ['ENG-SCI 153', 'PHYSICS 123', 'PHYSICS 223'],
   ['ENG-SCI 159', 'ENG-SCI 259'],
   ['ENG-SCI 177', 'ENG-SCI 277'],
   ['ENG-SCI 220', 'PHYSICS 220'],
   ['ENG-SCI 231', 'ENG-SCI 229'],
   ['ENGLISH CAMR', 'TDM CAMR'],
   ['ENGLISH CKR', 'TDM CKR'],
   ['ENGLISH 90DS', 'TDM 128X'],
   ['ENGLISH 90HT', 'HIST 84E'],
   ['ENGLISH 90TC', 'TDM 179P'],
   ['ENGLISH 282A', 'ROM-STD 235A'],
   ['ENGLISH 282B', 'ROM-STD 235B'],
   ['FOLKMYTH 114', 'TDM 144'],
   ['FOLKMYTH 160', 'SCAND 102'],
   ['FRENCH 192', 'MUSIC 192RR'],
   ['GERMAN 134', 'HIST 13K', 'MUSIC 192R'],
   ['GERMAN 140', 'HIST 1323'],
   ['GERMAN 143', 'HIST 1265'],
   ['GERMAN 254', 'VES 289'],
   ['GERMAN 262', 'HIST 2326'],
   ['GERMAN 291', 'ROM-STD 201'],
   ['GOV 1045', 'MUSIC 193R'],
   ['GOV 1093', 'SCRB 60'],
   ['GOV 1328', 'GOV 2328'],
   ['GOV 1430', 'GOV 2430'],
   ['GOV 2000', 'GOV 2000E', 'GOV 1000'],
   ['GOV 2001', 'GOV 1002'],
   ['GOV 2002', 'STAT 186'],
   ['HEB 1280', 'HEB 2480'],
   ['HIST 14L', 'SOC-STD 96SD'],
   ['HIST 2040', 'HISTSCI 240'],
   ['HISTSCI 194', 'VES 154G'],
   ['ISLAMCIV 138', 'RELIGION 1838'],
   ['ISLAMCIV 181', 'RELIGION 1812'],
   ['ISLAMCIV 184', 'RELIGION 1814'],
   ['ISLAMCIV 186', 'RELIGION 1816'],
   ['ISLAMCIV 204', 'PHIL 204'],
   ['ISLAMCIV 218', 'RELIGION 2810'],
   ['LATIN 133', 'MEDLATIN 133'],
   ['LATIN 134', 'LING 221R'],
   ['LATIN 162', 'MEDLATIN 162'],
   ['LIFESCI 100', 'MCB 100'],
   ['LIFESCI 120', 'MCB 120'],
   ['MCB 80', 'NEURO 80'],
   ['MCB 105', 'NEURO 105'],
   ['MCB 115', 'NEURO 115'],
   ['MCB 125', 'NEURO 125'],
   ['MCB 129', 'NEURO 129'],
   ['MCB 131', 'NEURO 131'],
   ['MCB 143', 'NEURO 143'],
   ['MCB 148', 'NEURO 148'],
   ['MCB 170', 'NEURO 170'],
   ['MEDVLSTD 106', 'NEC 106'],
   ['MICROBI 210', 'OEB 290'],
   ['NEURO 57', 'OEB 57'],
   ['NEURO 130', 'NEUROBIO 230'],
   ['NEURO 140', 'NEUROBIO 240'],
   ['NEURO 141', 'PHYSICS 141'],
   ['NEURO 1202', 'PSY 1202'],
   ['NEURO 1401', 'PSY 1401'],
   ['PERSIAN 108', 'RELIGION 1804'],
   ['PHIL 187', 'PHIL 287'],
   ['PHYSICS 123', 'PHYSICS 223'],
   ['PHYSICS 191', 'PHYSICS 247'],
   ['PSY 15', 'PSY 3515'],
   ['SLAVIC 98A', 'SLAVIC 158'],
   ['SLAVIC 98B', 'SLAVIC 148'],
   ['SLAVIC 114', 'TDM 114K'],
   ['SOCIOL 1112', 'SOCIOL 2112'],
   ['STAT 115', 'STAT 215'],
   ['STAT 160', 'STAT 260'],
   ['TDM 138D', 'VES 138D'],
   ['TDM 1135', 'WOMGEN 1135'],
   ['TDM 1229', 'WOMGEN 1229'],
   ['TDM 1246', 'WOMGEN 1246'],
]

_non_canon = set(c for l in [cl[1:] for cl in cross_listed_courses] for c in l)
def cross_list_canonical(cn):
    for cl in cross_listed_courses:
        if cn in cl:
            return cl[0]

    return cn

def is_cross_list_canonical(cn):
    return cn not in _non_canon