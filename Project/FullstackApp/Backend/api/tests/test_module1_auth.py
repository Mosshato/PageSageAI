"""
Module 1 — Authentication Performance Tests
============================================
Covers: POST /api/auth/signup, POST /api/auth/login, GET /api/auth/me,
        POST /api/auth/token/refresh/

Performance threshold: avg response ≤ 400 ms (local DB, no external calls).
Each benchmark repeats the request REPEAT times; timing stats are printed.
"""
from django.contrib.auth import get_user_model

from .base import PerfTestCase, REPEAT

User = get_user_model()
SIGNUP_URL  = '/api/auth/signup/'
LOGIN_URL   = '/api/auth/login/'
ME_URL      = '/api/auth/me/'
REFRESH_URL = '/api/auth/token/refresh/'


class AuthFunctionalTests(PerfTestCase):
    """Correctness: every auth endpoint returns the expected status code."""

    def test_signup_valid(self):
        payload = {
            'firstName': 'Alice', 'lastName': 'Smith',
            'email': 'alice@test.com', 'password': 'secure123',
            'role': 'student',
        }
        res = self.client.post(SIGNUP_URL, payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIn('token', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['role'], 'student')

    def test_signup_duplicate_email(self):
        payload = {
            'firstName': 'T', 'lastName': 'T',
            'email': 'teacher@test.com', 'password': 'pass1234',
            'role': 'teacher',
        }
        res = self.client.post(SIGNUP_URL, payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_signup_invalid_role(self):
        payload = {
            'firstName': 'X', 'lastName': 'X',
            'email': 'x@test.com', 'password': 'pass1234',
            'role': 'admin',
        }
        res = self.client.post(SIGNUP_URL, payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_login_valid(self):
        res = self.client.post(LOGIN_URL,
            {'email': 'teacher@test.com', 'password': 'pass1234', 'role': 'teacher'},
            format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', res.data)
        self.assertEqual(res.data['user']['email'], 'teacher@test.com')

    def test_login_wrong_password(self):
        res = self.client.post(LOGIN_URL,
            {'email': 'teacher@test.com', 'password': 'wrong', 'role': 'teacher'},
            format='json')
        self.assertEqual(res.status_code, 401)

    def test_login_role_mismatch(self):
        res = self.client.post(LOGIN_URL,
            {'email': 'teacher@test.com', 'password': 'pass1234', 'role': 'student'},
            format='json')
        self.assertEqual(res.status_code, 401)

    def test_me_authenticated(self):
        self.auth_teacher()
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['user']['email'], 'teacher@test.com')

    def test_me_unauthenticated(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, 401)

    def test_token_refresh(self):
        login = self.client.post(LOGIN_URL,
            {'email': 'student@test.com', 'password': 'pass1234', 'role': 'student'},
            format='json')
        refresh_token = login.data['refresh']
        res = self.client.post(REFRESH_URL, {'refresh': refresh_token}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)


class AuthPerformanceTests(PerfTestCase):
    """
    Performance: each endpoint is called REPEAT times; average must be ≤ 400 ms.
    Results are printed to stdout for thesis documentation.
    """

    def test_perf_login(self):
        """
        Login involves bcrypt password verification (intentionally slow for security).
        Threshold is set to 2000 ms to accommodate the cost of one bcrypt round.
        """
        payload = {'email': 'teacher@test.com', 'password': 'pass1234', 'role': 'teacher'}
        stats = self.measure(
            lambda: self.client.post(LOGIN_URL, payload, format='json'), n=REPEAT)
        self.assert_perf(stats, 'POST /api/auth/login/ (bcrypt)', threshold_ms=2000)

    def test_perf_me(self):
        self.auth_teacher()
        stats = self.measure(lambda: self.client.get(ME_URL), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/auth/me/')

    def test_perf_token_refresh(self):
        login = self.client.post(LOGIN_URL,
            {'email': 'student@test.com', 'password': 'pass1234', 'role': 'student'},
            format='json')
        token = login.data['refresh']
        stats = self.measure(
            lambda: self.client.post(REFRESH_URL, {'refresh': token}, format='json'),
            n=REPEAT)
        self.assert_perf(stats, 'POST /api/auth/token/refresh/')

    def test_perf_signup(self):
        """Signup involves bcrypt hashing; threshold is 2000 ms."""
        counter = [0]

        def do_signup():
            counter[0] += 1
            self.client.post(SIGNUP_URL, {
                'firstName': 'Perf', 'lastName': 'User',
                'email': f'perf{counter[0]}@test.com',
                'password': 'pass1234', 'role': 'student',
            }, format='json')

        stats = self.measure(do_signup, n=REPEAT)
        self.assert_perf(stats, 'POST /api/auth/signup/ (bcrypt)', threshold_ms=2000)
