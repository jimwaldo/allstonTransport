12/27/18

Splitting by term has simplified things considerably-- the class nums are unique within a semester. A course may 
have different class nums associated with it; these will be the sections of the course, many of which have times
that are separate. I've also given up on getting the right set of faculty huids to use to identify the classes
that will be in Allston-- instead, I will use the subject field and assume that any class in particular subjects 
(such as COMPSCI, APCOMP, or APMTH) will be taught in Allston.

The data layout for the enrollment .csv files is:

0 TERM

1 CLASS_NUM

2 COURSE_ID

3 SUBJECT

4 CATALOG

5 SECTION

6 DESCRIPTION

7 COMPONENT

8 STUDENT

9 INSTRUCTOR 

I now set up a program that will generate three sets (and save them as .pkl files) for each semester. Using a file
that contains the set of subjects that will be taught in Allston (currently called seas_subjects_s.pkl, and containing
the set of APCOMP, APMTH, and COMPSCI) the program split_classes_students generates the set of all classes that are
in these subjects and the huid of all of the students who took these classes. The program then generates the set of
all the courses taken in any subject by the students who took one of the courses in the seas subjects. The set of all
the classes that will be taught in Allston is saved in the file SEAS_class_set.pkl; the set of all the students who
are in at least one of those classes is saved in the file SEAS_student_set.pkl, and the set of all the classes taken by 
any of these students is saved in the file all_seas_student_classes_set.pkl. 

12/26/18

Realized that things would be a lot simpler if I extracted the courses and times for each semester and treated 
them separately. Since none of the analysis requires moving across semesters, this will make the files a lot 
smaller and will only need to have repeated application of the same programs to get the analysis. Should have 
thought of this sooner.

First I split the enrollment and course time files up into one file for each semester. This had the added benefit 
of removing the ambiguity in the course numbering— now there is no class_num that is different from the 
course_num/class_num combination.

Every semester there are a number of classes that don’t have an associated time. On first look it appears that 
most of these are either cross-reg courses or seminars, but I’ll have to see. 


12/25/18
So far I’ve been assuming that the class_num is not re-used. But that turns out not to be true. The class_num 
gets reused, often for an offering of the same class in a different semester, but also for a completely different 
class in a different semester. For the same semester, the class_id is sometimes re-used to show a different time 
for the same course; this happens for a lot of tutorials, but also happens for lectures in German. There are 256 
duplicate term/class_num combinations that are at different times. These are saved in the file 
repeat_class_term_set.pkl.

This means that I needed to re-calculate the classes potentially taught in Allston, keying the classes by the 
combination of the term and the class_num. This ended up with 800 classes, stored in allston_class_term_set.pkl. 

I then had to re-calculate the students in these courses. Keying on the term/class_id led to a set of 7,358 
students, which was saved in allston_student.pkl. Re-calculating all the classes these students took resulted in 
18,353 class/term combinations. Fortunately, none of these classes are in the set of class_num/term that has 
multiple times. This set of term/class_num was saved in allston_st_class_set.pkl. Note that there are a total of 
28,029 term/class_num combinations, or a little under 10k class/term combinations that no one taking one of the 
courses that will be in Allston take. 

Even using the concatenation of term + class_id + course_id there are 3,413 classes that students who would be in 
Allston would take but are not in the time listing. 

12/23/18
Using clean_csv.py to purge the csv files of lines that can’t be read (generally because of bad characters, 
probably the result of MS characters being exported from the registrar) I created an enrollment csv 
(courseEnrollmentsCleaned.csv) and a set of course times (courseTimesCleaned.csv). For course enrollments, there 
were 444,687 lines in the cleaned file (34 deleted); for the course times there were 23,270 course/times (27 
lines deleted). 

David Hwang provided a file of names of all faculty that might teach in Allston and their huids; this was taken 
from a list of all ladder and non-ladder faculty that were identified by David as teaching in Allston. Some of 
these (like Joe Blitzstein) may also teach in Cambridge when the Allston building opens, but that simply needs 
to be noted. A set of those faculty huids (which is the key in the course csv) is saved in fac_huid_set.pkl.

Using these huids, I built a set of all the classes (which are individual instances of a course) that are taught 
by any of the faculty in the fac_huid_set. There are 763 such courses. I then built a set of all of the students 
who took any of those classes; there are 15,036 such students.

Having gotten a set of all the students who would be taking a class from faculty who teach in Allston, we then 
form a set of all of the classes that these students have taken. This results in a set of 14,504 classes. 

12/15/18

Looking at the huids for faculty, there is a lot missing in the .csv file sent from the registrar. The enrollment 
information has 2,536 huids listed for instructors; the number of entries in the name to huid file sent by the 
registrar is 1,384. So about half of the names are missing. Further, there is a difference in the ways the names 
are represented in the files I’ve gotten from SEAS on who are the faculty and the way they are listed in the 
registrars database (and it doesn’t seem all that regular; Frank Doyle is listed as Francis Doyle, but SEAS list 
Edward Kohler while the registrar lists Eddie). 

So I’m going to try a new approach. I’ll start by putting together a list of all those teaching SEAS courses that 
will be in Allston, which has been suppled by David Hwang. From the name->huid listing I’ve gotten from the registrar, I’ll see how many of those names I can map to HUIDs. I will then send a list to the registrar, asking for the huids of the remaining names. For those that aren’t in the Allston list, it doesn’t really matter if I have their HUID or not. 

This may miss some faculty that are no longer teaching, but would be a reasonable first approximation.

Another possibility would be to do the identification of courses by their subject— all APCOMP, APMTH, COMPSCI, 
and the like. We could then gather all of the courses in these subjects, and then look at the collection of 
students who took at least one of these courses. This might miss some big courses (like Stat 110), but if we know 
which ones those are we could special-case them by manually adding them to the set of courses we are looking for. 
This would require building a set of all of the courses, but this wouldn’t be all that hard. This also won’t 
account for those subjects (like MSME) that are split between the two campuses. But again it would give a first 
approximation.

Doing this with a subject set of 'APCOMP', 'APMTH', 'APPHY', 'COMPSCI', 'ESE' results in 207 courses and 908 
classes. 