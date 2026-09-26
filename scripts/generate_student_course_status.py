"""Build a deterministic synthetic end-of-semester snapshot from the CSV inputs.

This is test data, not academic records provided by the school.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import random
import uuid


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def encode(fields, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')


def build(students, courses):
    by_curriculum = defaultdict(list)
    for course in courses:
        by_curriculum[course['curriculum_code']].append(course)
    statuses, adjusted, mismatches = [], [], []
    for student in students:
        sid = student['student_id']
        curriculum = by_curriculum.get(student['curriculum_code'])
        if not curriculum:
            raise ValueError(f'Missing curriculum courses for {sid}')
        semester = int(student['current_semester'])
        rng = random.Random(int.from_bytes(hashlib.sha256(('ojt-status-v1:'+sid).encode()).digest(), 'big'))
        eligible = [c for c in curriculum if 1 <= int(c['recommended_semester']) <= semester and int(c['credits']) > 0 and '_COM*' not in c['course_id'] and '_ELE' not in c['course_id']]
        # Weighted scenarios: 30% no failures, 40% one/two, 30% three/four/five.
        failed_count = rng.choices([0,1,2,3,4,5], weights=[30,20,20,15,10,5], k=1)[0]
        failed = {c['course_id'] for c in rng.sample(eligible, min(failed_count,len(eligible)))}
        credits = 0
        for course in curriculum:
            if int(course['recommended_semester']) > semester:
                status = 'NOT_TAKEN'
            elif course['course_id'] in failed:
                status = 'FAILED'
            else:
                status = 'PASSED'
                credits += int(course['credits'])
            statuses.append(dict(student_id=sid,academic_term=student['academic_term'],course_id=course['course_id'],status=status))
        updated = dict(student)
        updated['accumulated_credits'] = str(credits)
        adjusted.append(updated)
        if float(student['accumulated_credits']) != credits:
            mismatches.append(dict(student_id=sid,academic_term=student['academic_term'],original_accumulated_credits=student['accumulated_credits'],passed_course_credits=credits))
    return statuses, adjusted, mismatches


def validate(students, courses, statuses):
    course_lookup = {(c['curriculum_code'],c['course_id']):c for c in courses}
    assert len(course_lookup)==len(courses), 'Duplicate curriculum course'
    lookup = {(s['student_id'],s['academic_term']):s for s in students}
    assert len(lookup)==len(students), 'Duplicate student snapshot'
    assert len({(r['student_id'],r['academic_term'],r['course_id']) for r in statuses})==len(statuses)
    counts = Counter()
    for row in statuses:
        student = lookup[(row['student_id'],row['academic_term'])]
        course = course_lookup[(student['curriculum_code'],row['course_id'])]
        future = int(course['recommended_semester']) > int(student['current_semester'])
        assert row['status'] in {'PASSED','FAILED','NOT_TAKEN'}
        assert (row['status']=='NOT_TAKEN')==future
        counts[(row['student_id'],row['academic_term'])]+=1
    expected = Counter(c['curriculum_code'] for c in courses)
    assert all(counts[key]==expected[s['curriculum_code']] for key,s in lookup.items())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('repo',type=Path)
    parser.add_argument('--sync-credits',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    directory=args.repo/'data/dataset'
    fields, students=read(directory/'student.csv')
    _, courses=read(directory/'curriculum_courses.csv')
    statuses,adjusted,mismatches=build(students,courses)
    validate(students,courses,statuses)
    summary=dict(synthetic=True,snapshot='END_OF_CURRENT_SEMESTER',students=len(students),rows=len(statuses),status_counts=dict(Counter(r['status'] for r in statuses)),credit_mismatches=len(mismatches),sync_credits=args.sync_credits)
    print(json.dumps(summary,ensure_ascii=True))
    if args.dry_run:
        return
    report_dir=args.repo/'output/data_checks'
    report_dir.mkdir(parents=True,exist_ok=True)
    outputs={directory/'student_course_status.csv':encode(['student_id','academic_term','course_id','status'],statuses)}
    if args.sync_credits:
        outputs[directory/'student.csv']=encode(fields,adjusted)
    if mismatches:
        outputs[report_dir/'student_course_status.credit_reconciliation.csv']=encode(list(mismatches[0]),mismatches)
    backup_dir=args.repo/'data/backups'/('student-status-'+uuid.uuid4().hex)
    backup_dir.mkdir(parents=True)
    original={p:p.read_bytes() if p.exists() else None for p in outputs}
    # Check locks before modifying any target.
    for p in outputs:
        if p.exists():
            with p.open('r+b'):
                pass
    for p,content in original.items():
        if content is not None:
            (backup_dir/p.name).write_bytes(content)
    written=[]
    try:
        for p,content in outputs.items():
            p.write_bytes(content)
            written.append(p)
            assert p.read_bytes()==content
        _,saved=read(directory/'student_course_status.csv')
        assert saved==statuses
        if args.sync_credits:
            _,saved_students=read(directory/'student.csv')
            assert saved_students==adjusted
    except Exception:
        for p in written:
            if original[p] is not None:
                p.write_bytes(original[p])
        raise
    (report_dir/'student_course_status.summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
