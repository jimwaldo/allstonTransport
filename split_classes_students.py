
import csv, sys, pickle
import make_name_dicts as mnd

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python split_classes_students.py enrollment_file.csv seas_subject_set_file.pkl')
        sys.exit(1)

    fname = sys.argv[1]
    fin = open(fname, 'r')
    cin = csv.reader(fin)
    f_p = open(sys.argv[2], 'rb')
    seas_subject_s = pickle.load(f_p)
    f_p.close()


    h = next(cin)
    student_s = set()
    seas_class_s = set()
    all_seas_student_class_s = set()

    for l in cin:
        if l[3] in seas_subject_s:
            seas_class_s.add(l[1])
            student_s.add(l[8])

    fin.seek(0)
    h = next(cin)
    for l in cin:
        if l[8] in student_s:
            all_seas_student_class_s.add(l[1])
    fin.close()

    mnd.pickle_data('SEAS_class_set.pkl', seas_class_s)
    mnd.pickle_data('SEAS_student_set.pkl', student_s)
    mnd.pickle_data('all_seas_student_classes_set.pkl', all_seas_student_class_s)
