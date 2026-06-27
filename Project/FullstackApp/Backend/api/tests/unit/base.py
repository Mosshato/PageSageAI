"""
Shared base class for PageSage AI API performance tests.
Provides timing utilities, statistical aggregation, and common test data factories.
"""
import time
import statistics

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

REPEAT = 100        # number of repetitions per benchmark
THRESHOLD_MS = 400  # acceptable average response time (ms)


class PerfTestCase(TestCase):
    """
    Base class for all performance tests.
    Subclasses inherit the APIClient, two demo users (teacher + student),
    and the measure/assert_perf helpers.
    """

    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            email='teacher@test.com', password='pass1234',
            role='teacher', first_name='Test', last_name='Teacher',
        )
        cls.student = User.objects.create_user(
            email='student@test.com', password='pass1234',
            role='student', first_name='Test', last_name='Student',
        )

    def setUp(self):
        self.client = APIClient()

    # ── helpers ──────────────────────────────────────────────────────────────

    def auth_teacher(self):
        self.client.force_authenticate(user=self.teacher)

    def auth_student(self):
        self.client.force_authenticate(user=self.student)

    def measure(self, fn, n=REPEAT):
        """Run fn() n times and return timing stats (ms)."""
        times = []
        for _ in range(n):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
        return {
            'avg':    round(statistics.mean(times), 1),
            'min':    round(min(times), 1),
            'max':    round(max(times), 1),
            'median': round(statistics.median(times), 1),
            'stdev':  round(statistics.stdev(times) if n > 1 else 0, 1),
        }

    def assert_perf(self, stats, label, threshold_ms=THRESHOLD_MS):
        """Assert average response time is within threshold and print results."""
        print(
            f'\n    [PERF] {label:50s} '
            f'avg={stats["avg"]:6.1f}ms  '
            f'min={stats["min"]:6.1f}ms  '
            f'max={stats["max"]:6.1f}ms  '
            f'sd={stats["stdev"]:5.1f}ms'
        )
        self.assertLess(
            stats['avg'], threshold_ms,
            f'{label}: avg {stats["avg"]}ms > threshold {threshold_ms}ms',
        )
