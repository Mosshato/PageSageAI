"""
Module 2 — Class, Enrollment, Assignment & Submission Performance Tests
=======================================================================
Covers: GET/POST /api/classes/, POST /api/classes/enroll/, DELETE /api/classes/<id>/quit/,
        GET /api/assignments/, POST /api/assignments/<id>/submit/,
        DELETE /api/assignments/<id>/unsubmit/, GET /api/account/stats/

Performance threshold: avg response ≤ 400 ms (all operations are pure DB, no I/O).
"""
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import Class, Enrollment, Assignment, Submission

from .base import PerfTestCase, REPEAT


def make_class(teacher):
    return Class.objects.create(
        name='Test Class', teacher_name='Test Teacher',
        teacher=teacher, color='#3b82f6', icon='📖',
    )


class ClassFunctionalTests(PerfTestCase):
    """Correctness tests for class and enrollment endpoints."""

    def setUp(self):
        super().setUp()
        self.cls = make_class(self.teacher)
        Enrollment.objects.create(
            class_obj=self.cls,
            student_email=self.student.email,
            student_name='Test Student',
        )

    def test_student_class_list(self):
        self.auth_student()
        res = self.client.get('/api/classes/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_enroll_valid_code(self):
        new_cls = make_class(self.teacher)
        self.auth_student()
        res = self.client.post('/api/classes/enroll/', {'code': new_cls.code}, format='json')
        self.assertEqual(res.status_code, 201)

    def test_enroll_invalid_code(self):
        self.auth_student()
        res = self.client.post('/api/classes/enroll/', {'code': 'XXXXXX'}, format='json')
        self.assertEqual(res.status_code, 404)

    def test_enroll_duplicate(self):
        self.auth_student()
        res = self.client.post('/api/classes/enroll/', {'code': self.cls.code}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_class_detail(self):
        self.auth_student()
        res = self.client.get(f'/api/classes/{self.cls.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['id'], self.cls.id)

    def test_quit_class(self):
        self.auth_student()
        res = self.client.delete(f'/api/classes/{self.cls.id}/quit/')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(
            Enrollment.objects.filter(class_obj=self.cls, student_email=self.student.email).exists()
        )


class AssignmentFunctionalTests(PerfTestCase):
    """Correctness tests for assignment and submission endpoints."""

    def setUp(self):
        super().setUp()
        self.cls = make_class(self.teacher)
        Enrollment.objects.create(
            class_obj=self.cls,
            student_email=self.student.email,
            student_name='Test Student',
        )
        self.assignment = Assignment.objects.create(
            class_obj=self.cls,
            title='Homework 1',
            description='Solve problems 1-5',
            due_date='2026-07-15',
            status='pending',
        )

    def test_all_assignments(self):
        self.auth_student()
        res = self.client.get('/api/assignments/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_submit_assignment(self):
        self.auth_student()
        pdf = SimpleUploadedFile('hw.pdf', b'%PDF-1.4 content', content_type='application/pdf')
        res = self.client.post(
            f'/api/assignments/{self.assignment.id}/submit/',
            {'files': pdf}, format='multipart',
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            Submission.objects.filter(
                assignment=self.assignment, student_email=self.student.email
            ).exists()
        )

    def test_submit_without_file(self):
        self.auth_student()
        res = self.client.post(f'/api/assignments/{self.assignment.id}/submit/',
                               {}, format='multipart')
        self.assertEqual(res.status_code, 400)

    def test_unsubmit_assignment(self):
        Submission.objects.create(
            assignment=self.assignment, student_email=self.student.email)
        self.auth_student()
        res = self.client.delete(f'/api/assignments/{self.assignment.id}/unsubmit/')
        self.assertEqual(res.status_code, 200)

    def test_account_stats_no_submissions(self):
        self.auth_student()
        res = self.client.get('/api/account/stats/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('classes_count', res.data)


class ClassPerformanceTests(PerfTestCase):
    """Performance benchmarks for Module 2 endpoints."""

    def setUp(self):
        super().setUp()
        self.cls = make_class(self.teacher)
        Enrollment.objects.create(
            class_obj=self.cls,
            student_email=self.student.email,
            student_name='Test Student',
        )
        self.assignment = Assignment.objects.create(
            class_obj=self.cls, title='HW', description='desc',
            due_date='2026-07-15', status='pending')

    def test_perf_class_list(self):
        self.auth_student()
        stats = self.measure(lambda: self.client.get('/api/classes/'), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/classes/')

    def test_perf_class_detail(self):
        self.auth_student()
        url = f'/api/classes/{self.cls.id}/'
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/classes/<id>/')

    def test_perf_all_assignments(self):
        self.auth_student()
        stats = self.measure(lambda: self.client.get('/api/assignments/'), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/assignments/')

    def test_perf_account_stats(self):
        self.auth_student()
        stats = self.measure(lambda: self.client.get('/api/account/stats/'), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/account/stats/')
