The code in this project is designed to read files containing enrollment data and class 
time data supplied by the registrar and determine the number of students who will have to 
cross the Charles based on assumptions of which classes will be taught in the new SEC building.
Note that the model used here is crude and will give at best a rough approximation of what the
traffic will actually be.

##### Input files

This code works on files supplied by the registrar/my.harvard group. There are two kinds of .csv files provided, the
enrollment files and the course-time files. The enrollment files have one line per student enrolled in a course, with
each line having the following format (where the number indicates the index of the field, followed by the description):

0 TERM in the format YYYY {Spring,Fall}

1 CLASS_NUM A numeric identifier for the class. A single course may have many classes (think of this as a section)

2 COURSE_ID A numeric identifier for the course. This is unique within a term, but may be re-used for a different class
in other terms

3 SUBJECT The department or program offering the course, seems to always be all-caps, for example PHIL

4 CATALOG The number of the course within the subject, for example 303

5 SECTION A numeric indicating the subject. Multiple instances with the same class_num and course_id may have the 
same section number. 

6 DESCRIPTION A textual description of the course 

7 COMPONENT A textual description of the type of course (lecture, lab, etc.)

8 STUDENT the HUID of the student enrolled in the course

9 INSTRUCTOR the HUID of the instructor of the course.

The second file used is the course_time.csv file, that contains information on when the courses are taught. This file has
the format:

0 TERM The term the course was taught, as in the enrollment file

1 CLASS_NUM the class number, as in the enrollment file

2 COURSE_ID the course identifier, as in the enrollment file

3 SUBJECT the department or program offering the course, as in the enrollment file

4 CATALOG the catalog number within the department or program, as in the enrollment file

5 SECTION the section number, as in the enrollment file

6 DESCRIPTION a textual description, as in the enrollment file

7 COMPONENT A textual description of the type of course (lecture, lab, etc.), as in the enrollment file

8 Mtg Start The time the course starts, in the text format hh:mm:ss {AM/PM}. Not all classes have a start time, so this
might be blank. Also note that ss is always 00

9 Mtg End The time the course ends, in the same text format as the Mtg Start time

10 Mon Y if the class meets on Monday, N otherwise

11 Tues Y if the class meets on Tuesday, N otherwise

12 Wed Y if the class meets on Wednesday, N otherwise

13 Thurs Y if the class meets on Thursday, N otherwise

14 Fri Y if the class meets on Friday, N otherwise

15 Sat Y if the class meets on Saturday, N otherwise

16 Sun Y if the class meets on Sunday, N otherwise

Note: almost no classes are scheduled to meet on Saturday or Sunday; in Fall of 2015, for example, only four discussion
sections met on Sunday and no class met on Saturday.

Given that there was no consistent way to identify courses over different semesters (at least that I could find in the
files) the first step of the analysis was to break the enrollent.csv file and the course_time.csv file (each of which
came from the registrar as a single file covering multiple years) into separate files, one for each semester.

######Running the programs

Starting with the enrollment.csv and class_time.csv files supplied by the registrar, and after appropriate cleaning with
clean_csv.py and split_by_term.py, the first program to be run is split_by_term.py, that will split the enrollment and 
course time files into directories, one for each term, containing an enrollment.csv and course_time.csv file for the 
courses taught that term.

The next program to run is split_classes_students.py. This takes as input the 
enrollment.csv file and a python pickle of the set of subjects (department/programs) whose classes will be taught in 
Allston. **This needs to change; the set of classes should be made an input to this.** This will produce three files:

1. Allston_class_set.pkl, which contains a pickle of the set of classes indicated as being taught in Allston

2. Allston_student_set.pkl, which contains a pickle of the set of students who have a class in Allston

3. all_allston_student_classes_set.pkl, which contains a pickle of all classes (taught anywhere) taken by the students
who take a least one class in Allston.

From this point on, none of the following programs take any command-line arguments; all work with generated files. Which
files are generated and which are read is specified, but only for purposes of debugging.

Next, build a dictionary of courses and class times using build_course_times.py, which takes the course_times.csv file 
supplied by the registrar, the set of all classes taken by students who take any class in Allston produced by 
split_classes_students.py (all_allston_student_classes_set.pkl) and the set of all courses taught in Allston produced by
split_classes_students.py (Allston_class_set.pkl). This will generate class_time_d.pkl, a dictionary indexed by
class with value a course_time object that has the course, time at which the course meets, where the course meets, and
the days of the week that the course meets.

Next run student_schedule.py, which builds a dictionary, indexed by student, of the schedule for each student that takes
a course that meets in Allston. The program takes the set of students who take a course in Allston that was
generated by split_classes_students.py (Allston_student_set.pkl), the enrollments.csv file supplied by the registrar, and 
the dictionary of class times generated by build_course_times.py (class_time_d.pkl). The resulting dictionary
is written to a file named student_schedule_d.pkl.

Next run build_transition_d.py, which takes the student_schedule_d.pkl file produced by student_schedule.py.
This will produce a dictionary keyed by student id that shows the transitions across the river for each time and day
for that student, written to the file transition_d.pkl

Finally, run build_transition_time_d.py that will build a list of dictionaries, one for each day, keyed by time with a 
count of the number of transitions from Cambridge to Allston and from Allston to Cambridge on that day and time. This 
program takes the file name of the transition dictionary produced by build_transition_d.py, named
transition_d.pkl, and will produce a file trans_time_d_l.pkl.

There are two programs that can be used to get the information in a readable form:

1. **make_csv_transitions.py**: Creates a .csv file that can be viewed in a spreadsheet. The file will, for each day,
show the time, number of students needing to move from Cambridge to Allston at that time, and the number of students
needing to move from Cambridge to Allston. This program takes as a command line argument the name of the .csv file
that should be created with the output.

2. **display_trans.py**: Produces a (bad) bar chart displaying the data. Takes as an argument a string that will be
used as a title for the chart. 


#####Programs in the project:

**clean_csv.py**: Reads a .csv file and writes a copy of that file, leaving out any lines of the
original that will throw an exception when read as a csv. There are a number of lines in the data
from my.harvard that throw exceptions, generally because of characters that are outside of the
utf-8 character set. I believe this is a hold-over from the course names and descriptions that
were supplied from the various departments, many of which were simply pasted in from a MS-word
document and contained characters from the MS character set that are not utf-8. The program 
will print out the total number of lines read, the number of lines written to the new file, and
the number of lines discarded.

**split_by_term.py**: Reads a csv file in which the first field is the term identifier, and splits the csv file into
a set of csv files, where each of the output files contains the entries for a single term.

**make_name_dicts.py**: Somewhat mis-named, contains a collection of utility functions that are
used throughout the rest of the code. Not all of these functions are still being used.

**check_unique_class.py**: Quick and dirty check to see if the combination of course_num and course_id in the enrollment
file added any information. It does not appear to from this check.

**split_classes_students.py**: Creates three sets that are used by the rest of the programs. The first is the set of 
class_num identifiers that are being modeled as being taught in Allston. Currently, this is determined by whether or not 
these are in the fields that are assumed to be in Allston (COMPSCI, APCOMP, APMTH). Any class_num that is in these
subjects is placed in the Allston class set. At the same time, any student who is taking one of these classes is placed
into a set of all students who are taking classes in Allston. Finally, a second pass is made over the enrollment file,
and a set of all of the class_num that are taken by any student who is taking a class in Allston is created.

***Currently, the subject_set pickle is created by hand. An obvious enhancement would be to have a way of generating a set
of the classes that are going to be in Allston which would give finer-grained control over the model.***

**build_course_times.py**: Builds a dictionary indexed by the class_num that has as value a course_time object (define
in class_time.py). A course_time object contains the normalized start and end time of the course, where the course is
taught (either Allston or Cambridge), and the days of the week that the course meets. This program takes the course_time
file for the semester extracted from the file supplied by the registrar, a file containing the python pickle of the set 
of all classes being taken by any students who take any class in Allston (built by running split_classes_students.py) 
and the name of a file containing the python pickle of the set of classes that will be taught in Allston (also produced 
by split_classes_students.py).

**student_schedule.py**: Builds a dictionary indexed by student id for a set of students, with values a student_schedule 
object for that student for the semester. The schedule object (defined in class_time.py) contains the student number, the
set of classes the student takes, and an list of lists, one for each day of the week, of the classes the student takes
including start time, end time, and location (Allston or Cambridge).

**build_transition_d.py**: Using the student schedules built by student_schedule.py, builds a dictionary that allows
calculation of the transitions from Allston to Cambridge and back. The dictionary built is keyed by student HUID, and
has as a value a transition object for each time the student crosses the river. The transition object, defined in
class_time.py, contains a list transitions for each day, kept as a list. It also has a list of tr_time objects, which 
indicate when the student has to cross the river and in which direction (the destination). 

**build_transition_times_d.py**: Using the data built by build_transition_d.py, builds a list of dictionaries, one for 
each day, that is indexed by the time of day with values a list of two integers. The first is the number of students 
travelling from Cambridge to Allston at that time; the second is the number of students travelling from Allston to 
Cambridge at that time.

**display_trans.py**: Takes the list of dictionaries of times and transitions built by build_transition_times_d.py and 
creates a simple bar chart of the times and number of transitions for each day of the week.

**make_csv_transitions.py**: Create a csv file from the output of build_transition_times_d.py. This is an alternative to
display_trans.py, that creates a file that can be read into a spreadsheet and may be easier to read than the graphs in
display_trans_py.