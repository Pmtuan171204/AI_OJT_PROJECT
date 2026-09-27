"""Generate a conditional semester-five plan from curriculum data, not registrations."""
import argparse
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import uuid

FIELDS = ['student_id','academic_term','semester_number','course_id','credits_to_gain','plan_source']

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def build(students,courses,statuses,target_term):
    curriculum=defaultdict(list)
    course_keys=set()
    for course in courses:
        key=(course['curriculum_code'],course['course_id'])
        if key in course_keys:
            raise ValueError('Duplicate curriculum/course')
        course_keys.add(key)
        if int(course['recommended_semester'])==5:
            curriculum[course['curriculum_code']].append(course)
    status_lookup={}
    for row in statuses:
        key=(row['student_id'],row['academic_term'],row['course_id'])
        if key in status_lookup:
            raise ValueError('Duplicate student status')
        status_lookup[key]=row['status']
    result=[]
    seen=set()
    for student in students:
        sid=student['student_id']
        if sid in seen:
            raise ValueError('Expected one current snapshot per student')
        seen.add(sid)
        if int(student['current_semester'])!=4:
            raise ValueError(f'{sid}: this generator expects end-of-semester 4')
        if target_term==student['academic_term']:
            raise ValueError('Target term must differ from evaluation term')
        subjects=curriculum[student['curriculum_code']]
        if not subjects:
            raise ValueError(f'{sid}: missing semester 5 curriculum')
        for course in subjects:
            key=(sid,student['academic_term'],course['course_id'])
            if key not in status_lookup:
                raise ValueError(f'Missing current status for {key}')
            status=status_lookup[key]
            if status=='PASSED':
                continue
            if status!='NOT_TAKEN':
                raise ValueError(f'{key}: requires an individual plan for status {status}')
            result.append(dict(student_id=sid,academic_term=target_term,semester_number=5,
                               course_id=course['course_id'],credits_to_gain=int(course['credits']),
                               plan_source='CURRICULUM_ASSUMPTION'))
    if len({(r['student_id'],r['academic_term'],r['course_id']) for r in result})!=len(result):
        raise ValueError('Duplicate plan rows')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo',type=Path)
    parser.add_argument('--target-term',required=True,help='Explicit assumed next academic term')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    root=args.repo.resolve()
    students=read(root/'data/synthetic/student.csv')
    courses=read(root/'data/raw/curriculum_courses.csv')
    statuses=read(root/'data/synthetic/student_course_status.csv')
    rows=build(students,courses,statuses,args.target_term)
    counts=Counter(r['student_id'] for r in rows)
    summary={'synthetic':True,'target_term':args.target_term,'semester_number':5,
             'plan_source':'CURRICULUM_ASSUMPTION','students':len(students),
             'students_with_plan':len(counts),'rows':len(rows),
             'student_counts_by_plan_size':dict(Counter(counts.values())),
             'combo_slot_rows':sum('_COM*' in r['course_id'] or '_ELE' in r['course_id'] for r in rows),
             'assumptions':['Target term is an explicit scenario, not a verified school registration calendar.',
                            'No extra retakes from earlier semesters are added.',
                            'Combo/elective codes remain curriculum slots; individual choices are not known.']}
    print(json.dumps(summary,ensure_ascii=True))
    if args.dry_run:
        return
    path=root/'data/synthetic/student_study_plan.csv'
    if path.exists():
        # Verify that a spreadsheet application has not locked the destination.
        with path.open('r+b'):
            pass
        backup=root/'data/backups'/('study-plan-'+uuid.uuid4().hex)
        backup.mkdir(parents=True)
        (backup/path.name).write_bytes(path.read_bytes())
    buffer=io.StringIO(newline='')
    writer=csv.DictWriter(buffer,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(buffer.getvalue().encode('utf-8-sig'))
    assert read(path)==[{k:str(v) for k,v in r.items()} for r in rows]
    reports=root/'output/data_checks'
    reports.mkdir(parents=True,exist_ok=True)
    (reports/'student_study_plan.summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
