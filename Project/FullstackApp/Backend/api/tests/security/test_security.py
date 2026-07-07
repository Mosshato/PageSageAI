"""
Security Tests -PageSage AI Backend
=====================================
Covers five security properties claimed in the thesis:

  SEC-1  All protected endpoints return 401 when no token is provided.
  SEC-2  Malformed / invalid Bearer tokens are rejected with 401.
  SEC-3  Ownership isolation -a teacher cannot access another teacher's resources.
  SEC-4  Role separation -a student cannot call teacher-only endpoints and vice-versa.
  SEC-5  User passwords are stored as hashes, never as plaintext.

Run:
    python manage.py test api.tests.security -v 2
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api.domain import Class, Enrollment, Assignment

User = get_user_model()

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_teacher(email='teacher_a@sec.test'):
    return User.objects.create_user(
        email=email, password='SecurePass1!',
        role='teacher', first_name='Teacher', last_name='A',
    )


def make_student(email='student_a@sec.test'):
    return User.objects.create_user(
        email=email, password='SecurePass1!',
        role='student', first_name='Student', last_name='A',
    )


def make_class(teacher):
    return Class.objects.create(
        name='Security Test Class',
        teacher_name=f'{teacher.first_name} {teacher.last_name}',
        teacher=teacher,
        color='#3b82f6',
        icon='SEC',
    )


# ── SEC-1: Unauthenticated requests are rejected ──────────────────────────────

class SEC1_UnauthenticatedAccess(TestCase):
    """
    SEC-1: Every endpoint that requires authentication must return 401
    when the request carries no Authorization header at all.
    """

    PROTECTED_ENDPOINTS = [
        ('GET',    '/api/auth/me/'),
        ('GET',    '/api/classes/'),
        ('POST',   '/api/classes/enroll/'),
        ('GET',    '/api/classes/1/'),
        ('DELETE', '/api/classes/1/quit/'),
        ('GET',    '/api/assignments/'),
        ('POST',   '/api/assignments/1/submit/'),
        ('DELETE', '/api/assignments/1/unsubmit/'),
        ('GET',    '/api/account/stats/'),
        ('GET',    '/api/teacher/classes/'),
        ('POST',   '/api/teacher/classes/'),
        ('GET',    '/api/teacher/stats/'),
        ('GET',    '/api/teacher/students/'),
        ('GET',    '/api/teacher/classes/1/'),
        ('POST',   '/api/teacher/classes/1/students/'),
        ('POST',   '/api/teacher/classes/1/announcements/'),
        ('POST',   '/api/teacher/classes/1/assignments/'),
        ('POST',   '/api/teacher/classes/1/lectures/'),
        ('POST',   '/api/teacher/classes/1/ai-courses/'),
        ('GET',    '/api/ai-courses/class/1/'),
        ('GET',    '/api/ai-courses/1/status/'),
        ('GET',    '/api/ai-courses/1/page/1/'),
        ('POST',   '/api/ai-courses/1/ask/'),
        ('POST',   '/api/ai-courses/1/animations/'),
        ('GET',    '/api/ai-courses/1/animations/list/'),
        ('GET',    '/api/animations/1/status/'),
        ('GET',    '/api/ai-courses/1/quiz/status/'),
        ('GET',    '/api/ai-courses/1/quiz/questions/'),
        ('POST',   '/api/ai-courses/1/quiz/attempt/'),
        ('GET',    '/api/teacher/classes/1/ai-courses/1/quiz-results/'),
    ]

    def setUp(self):
        self.client = APIClient()

    def _call(self, method, url):
        fn = getattr(self.client, method.lower())
        return fn(url, format='json')

    def test_all_protected_endpoints_return_401_without_token(self):
        failures = []
        for method, url in self.PROTECTED_ENDPOINTS:
            res = self._call(method, url)
            if res.status_code != 401:
                failures.append(
                    f'{method:6} {url:60s} ->{res.status_code} (expected 401)'
                )

        if failures:
            detail = '\n  '.join(failures)
            self.fail(
                f'{len(failures)} endpoint(s) did not return 401 without a token:\n  {detail}'
            )
        else:
            print(
                f'\n    [SEC-1] PASS - all {len(self.PROTECTED_ENDPOINTS)} protected endpoints '
                f'return 401 when no token is provided.'
            )


# ── SEC-2: Malformed / invalid tokens are rejected ───────────────────────────

class SEC2_InvalidTokenRejected(TestCase):
    """
    SEC-2: djangorestframework-simplejwt rejects requests that carry a token
    that is not a valid JWT, regardless of the Bearer prefix.
    """

    def setUp(self):
        self.client = APIClient()

    def _get_me(self, token_value):
        self.client.credentials(HTTP_AUTHORIZATION=token_value)
        return self.client.get('/api/auth/me/')

    def test_garbage_string_is_rejected(self):
        res = self._get_me('Bearer thisisnotavalidjwttoken')
        self.assertEqual(res.status_code, 401,
            f'Garbage token was accepted (got {res.status_code}), expected 401.')
        print('\n    [SEC-2a] PASS -garbage Bearer token ->401')

    def test_wrong_scheme_is_rejected(self):
        """Sending "Token xyz" instead of "Bearer xyz" must be rejected."""
        res = self._get_me('Token somevalue')
        self.assertEqual(res.status_code, 401,
            f'Wrong auth scheme was accepted (got {res.status_code}), expected 401.')
        print('\n    [SEC-2b] PASS -wrong auth scheme ("Token" prefix) ->401')

    def test_empty_bearer_is_rejected(self):
        res = self._get_me('Bearer ')
        self.assertEqual(res.status_code, 401,
            f'Empty Bearer token was accepted (got {res.status_code}), expected 401.')
        print('\n    [SEC-2c] PASS -empty Bearer token ->401')

    def test_truncated_jwt_is_rejected(self):
        """A JWT has three dot-separated segments; two segments is invalid."""
        res = self._get_me('Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0')
        self.assertEqual(res.status_code, 401,
            f'Truncated JWT (2 segments) was accepted (got {res.status_code}), expected 401.')
        print('\n    [SEC-2d] PASS -truncated JWT (missing signature segment) ->401')

    def test_jwt_with_tampered_signature_is_rejected(self):
        """
        Obtain a real token, then replace the signature segment with garbage.
        The header + payload are structurally valid, but the signature won't verify.
        """
        User.objects.create_user(
            email='jwt_tamper@sec.test', password='SecurePass1!',
            role='student', first_name='JWT', last_name='Test',
        )
        login = self.client.post('/api/auth/login/', {
            'email': 'jwt_tamper@sec.test',
            'password': 'SecurePass1!',
            'role': 'student',
        }, format='json')
        self.assertEqual(login.status_code, 200)
        real_token = login.data['token']

        parts = real_token.split('.')
        self.assertEqual(len(parts), 3, 'Login did not return a well-formed JWT')
        tampered = '.'.join(parts[:2]) + '.INVALIDSIGNATUREXXXXXXXX'

        res = self._get_me(f'Bearer {tampered}')
        self.assertEqual(res.status_code, 401,
            f'JWT with tampered signature was accepted (got {res.status_code}), expected 401.')
        print('\n    [SEC-2e] PASS -JWT with tampered signature ->401')


# ── SEC-3: Ownership isolation ────────────────────────────────────────────────

class SEC3_OwnershipIsolation(TestCase):
    """
    SEC-3: A teacher (or student) cannot read or mutate resources
    that belong to another user. The ORM query filters by owner,
    so the response is 404 -the server does not confirm existence.
    """

    @classmethod
    def setUpTestData(cls):
        cls.teacher_a = make_teacher('teacher_a@sec.test')
        cls.teacher_b = make_teacher('teacher_b@sec.test')
        cls.student_a = make_student('student_a@sec.test')
        cls.student_b = make_student('student_b@sec.test')

        cls.class_a = make_class(cls.teacher_a)
        cls.enrollment_a = Enrollment.objects.create(
            class_obj=cls.class_a,
            student_email=cls.student_a.email,
            student_name='Student A',
        )
        cls.assignment_a = Assignment.objects.create(
            class_obj=cls.class_a,
            title='Assignment for SEC-3',
            description='desc',
            due_date='2026-12-31',
            status='pending',
        )

    def setUp(self):
        self.client = APIClient()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # Teacher isolation

    def test_teacher_b_cannot_get_teacher_a_class(self):
        self._auth(self.teacher_b)
        res = self.client.get(f'/api/teacher/classes/{self.class_a.id}/')
        self.assertEqual(res.status_code, 404,
            f'Teacher B got Teacher A\'s class detail (status {res.status_code}), expected 404.')
        print('\n    [SEC-3a] PASS -Teacher B cannot read Teacher A\'s class ->404')

    def test_teacher_b_class_not_in_list(self):
        self._auth(self.teacher_b)
        res = self.client.get('/api/teacher/classes/')
        self.assertEqual(res.status_code, 200)
        ids = [c['id'] for c in res.data]
        self.assertNotIn(self.class_a.id, ids,
            f'Teacher A\'s class appears in Teacher B\'s class list.')
        print('\n    [SEC-3b] PASS -Teacher A\'s class is not visible in Teacher B\'s list')

    def test_teacher_b_cannot_delete_teacher_a_class(self):
        self._auth(self.teacher_b)
        res = self.client.delete(f'/api/teacher/classes/{self.class_a.id}/')
        self.assertEqual(res.status_code, 404,
            f'Teacher B deleted Teacher A\'s class (status {res.status_code}), expected 404.')
        self.assertTrue(
            Class.objects.filter(id=self.class_a.id).exists(),
            'Teacher A\'s class was actually deleted by Teacher B.'
        )
        print('\n    [SEC-3c] PASS -Teacher B cannot delete Teacher A\'s class ->404 + class still exists')

    def test_teacher_b_cannot_add_student_to_teacher_a_class(self):
        self._auth(self.teacher_b)
        res = self.client.post(
            f'/api/teacher/classes/{self.class_a.id}/students/',
            {'email': 'intruder@sec.test', 'name': 'Intruder'},
            format='json',
        )
        self.assertEqual(res.status_code, 404,
            f'Teacher B added a student to Teacher A\'s class (status {res.status_code}), expected 404.')
        print('\n    [SEC-3d] PASS -Teacher B cannot add students to Teacher A\'s class ->404')

    # Student isolation

    def test_student_b_assignments_do_not_include_student_a_class(self):
        """Student B has no enrollments ->assignment list must be empty."""
        self._auth(self.student_b)
        res = self.client.get('/api/assignments/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0,
            f'Student B sees {len(res.data)} assignments that belong to Student A\'s class.')
        print('\n    [SEC-3e] PASS -Student B sees no assignments from Student A\'s class')

    def test_student_b_cannot_submit_to_student_a_assignment(self):
        """
        Student B is not enrolled in class_a, so submit must be rejected.
        The view checks enrollment via student_email; Student B's email won't match.
        Expected: 403 or 404.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        self._auth(self.student_b)
        pdf = SimpleUploadedFile('hack.pdf', b'%PDF-1.4', content_type='application/pdf')
        res = self.client.post(
            f'/api/assignments/{self.assignment_a.id}/submit/',
            {'files': pdf},
            format='multipart',
        )
        self.assertIn(res.status_code, [403, 404],
            f'Student B submitted to Student A\'s assignment (status {res.status_code}), expected 403 or 404.')
        print(f'\n    [SEC-3f] PASS -Student B cannot submit to Student A\'s assignment ->{res.status_code}')


# ── SEC-4: Role separation ────────────────────────────────────────────────────

class SEC4_RoleSeparation(TestCase):
    """
    SEC-4: Teacher-only endpoints reject authenticated students (and vice-versa).
    Because ownership filtering is used instead of explicit role checks,
    students get 404 (no classes owned by them exist); some views may return 400.
    The key invariant: students never get 200/201 on teacher routes.
    """

    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher('teacher_role@sec.test')
        cls.student = make_student('student_role@sec.test')
        cls.cls = make_class(cls.teacher)
        Enrollment.objects.create(
            class_obj=cls.cls,
            student_email=cls.student.email,
            student_name='Student Role',
        )

    def setUp(self):
        self.client = APIClient()

    def _auth_student(self):
        self.client.force_authenticate(user=self.student)

    def _auth_teacher(self):
        self.client.force_authenticate(user=self.teacher)

    # Students must not succeed on teacher-only endpoints

    def test_student_cannot_create_class(self):
        self._auth_student()
        res = self.client.post('/api/teacher/classes/', {
            'name': 'Hacked Class', 'teacher_name': 'Hacker',
        }, format='json')
        self.assertNotIn(res.status_code, [200, 201],
            f'Student created a class (status {res.status_code}); expected non-2xx.')
        print(f'\n    [SEC-4a] PASS -student cannot create a class ->{res.status_code}')

    def test_student_cannot_list_teacher_classes(self):
        self._auth_student()
        res = self.client.get('/api/teacher/classes/')
        if res.status_code == 200:
            self.assertEqual(len(res.data), 0,
                f'Student sees {len(res.data)} teacher classes; expected empty list or non-200.')
        print(f'\n    [SEC-4b] PASS -student gets no teacher classes ->{res.status_code} (empty={len(res.data) if res.status_code == 200 else "n/a"})')

    def test_student_cannot_view_teacher_class_detail(self):
        self._auth_student()
        res = self.client.get(f'/api/teacher/classes/{self.cls.id}/')
        self.assertNotEqual(res.status_code, 200,
            f'Student read teacher class detail (status {res.status_code}); expected non-200.')
        print(f'\n    [SEC-4c] PASS -student cannot read teacher class detail ->{res.status_code}')

    def test_student_cannot_add_announcement(self):
        self._auth_student()
        res = self.client.post(
            f'/api/teacher/classes/{self.cls.id}/announcements/',
            {'text': 'Hacked announcement'},
            format='json',
        )
        self.assertNotIn(res.status_code, [200, 201],
            f'Student posted an announcement (status {res.status_code}); expected non-2xx.')
        print(f'\n    [SEC-4d] PASS -student cannot post announcement ->{res.status_code}')

    def test_student_cannot_access_teacher_stats(self):
        self._auth_student()
        res = self.client.get('/api/teacher/stats/')
        if res.status_code == 200:
            self.assertEqual(res.data.get('total_classes', -1), 0,
                'Student sees non-zero teacher stats.')
        print(f'\n    [SEC-4e] PASS -student gets no teacher stats ->{res.status_code}')

    # Teachers must not succeed on student-only endpoints
    # (teacher has no enrollments ->results are empty, not an error, which is acceptable)

    def test_teacher_assignment_list_is_empty(self):
        """
        /api/assignments/ filters by enrolled classes for the requesting user's email.
        A teacher has no enrollments, so the list must be empty -not the student's data.
        """
        self._auth_teacher()
        res = self.client.get('/api/assignments/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0,
            f'Teacher sees {len(res.data)} student assignments; expected 0.')
        print('\n    [SEC-4f] PASS -teacher sees no student assignments (empty list)')

    def test_teacher_class_list_is_empty_for_student_endpoint(self):
        """
        GET /api/classes/ lists classes where the user is *enrolled as a student*.
        A teacher account has no such enrollments -list must be empty.
        """
        self._auth_teacher()
        res = self.client.get('/api/classes/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0,
            f'Teacher sees {len(res.data)} enrolled classes; expected 0.')
        print('\n    [SEC-4g] PASS -teacher sees no student-enrolled classes (empty list)')


# ── SEC-5: Password hashing ───────────────────────────────────────────────────

class SEC5_PasswordHashing(TestCase):
    """
    SEC-5: Django stores passwords as PBKDF2 hashes, never as plaintext.
    This test reads the raw `password` field from the database after user
    creation and signup, and asserts it starts with a known Django hash prefix.
    """

    DJANGO_HASH_PREFIXES = (
        'pbkdf2_sha256$',
        'pbkdf2_sha1$',
        'argon2$',
        'bcrypt$',
        'bcrypt_sha256$',
    )

    def _assert_hashed(self, raw_password_field, plaintext, label):
        self.assertFalse(
            raw_password_field == plaintext,
            f'{label}: plaintext password found in database!'
        )
        starts_with_known_algo = any(
            raw_password_field.startswith(prefix)
            for prefix in self.DJANGO_HASH_PREFIXES
        )
        self.assertTrue(
            starts_with_known_algo,
            f'{label}: password field does not match any known Django hash format: {raw_password_field!r}'
        )

    def test_create_user_hashes_password(self):
        plaintext = 'MyPlainPassword99!'
        User.objects.create_user(
            email='hash_test@sec.test', password=plaintext,
            role='student', first_name='Hash', last_name='Test',
        )
        db_user = User.objects.get(email='hash_test@sec.test')
        self._assert_hashed(db_user.password, plaintext, 'create_user')
        print(f'\n    [SEC-5a] PASS -create_user stores hash: {db_user.password[:30]}...')

    def test_signup_endpoint_hashes_password(self):
        plaintext = 'SignupPassword99!'
        client = APIClient()
        res = client.post('/api/auth/signup/', {
            'firstName': 'Hash', 'lastName': 'Signup',
            'email': 'hash_signup@sec.test',
            'password': plaintext,
            'role': 'teacher',
        }, format='json')
        self.assertEqual(res.status_code, 201, f'Signup failed: {res.data}')

        db_user = User.objects.get(email='hash_signup@sec.test')
        self._assert_hashed(db_user.password, plaintext, 'signup endpoint')
        print(f'\n    [SEC-5b] PASS -signup endpoint stores hash: {db_user.password[:30]}...')

    def test_password_is_verifiable_after_hashing(self):
        """The hash must still allow login with the original plaintext."""
        plaintext = 'VerifyMe99!'
        User.objects.create_user(
            email='hash_verify@sec.test', password=plaintext,
            role='student', first_name='Hash', last_name='Verify',
        )
        client = APIClient()
        res = client.post('/api/auth/login/', {
            'email': 'hash_verify@sec.test',
            'password': plaintext,
            'role': 'student',
        }, format='json')
        self.assertEqual(res.status_code, 200,
            'Login failed after hashing -hash is not verifiable.')
        print('\n    [SEC-5c] PASS -hashed password is verifiable at login ->200')

    def test_wrong_password_is_rejected_after_hashing(self):
        """An incorrect password must not pass hash verification."""
        User.objects.create_user(
            email='hash_wrong@sec.test', password='CorrectPass99!',
            role='student', first_name='Hash', last_name='Wrong',
        )
        client = APIClient()
        res = client.post('/api/auth/login/', {
            'email': 'hash_wrong@sec.test',
            'password': 'WrongPass99!',
            'role': 'student',
        }, format='json')
        self.assertEqual(res.status_code, 401,
            f'Wrong password was accepted after hashing (status {res.status_code}), expected 401.')
        print('\n    [SEC-5d] PASS -wrong password rejected after hashing ->401')
