"""
Module 5 — Concept Animation Performance Tests
===============================================
Covers: POST /api/ai-courses/<id>/animations/       (request animation)
        GET  /api/ai-courses/<id>/animations/list/  (animation library)
        GET  /api/animations/<id>/status/            (poll status)

`run_animation_in_background` is patched — no Manim/Gemini calls during tests.
Cache-hit behaviour (same concept requested twice) is also verified.
"""
import tempfile
import shutil
from unittest.mock import patch

from api.domain import Class, AICourse, ConceptAnimation

from .base import PerfTestCase, REPEAT

ANIM_URL   = lambda cid: f'/api/ai-courses/{cid}/animations/'
LIST_URL   = lambda cid: f'/api/ai-courses/{cid}/animations/list/'
STATUS_URL = lambda aid: f'/api/animations/{aid}/status/'


def make_ready_course(teacher, tmpdir):
    cls = Class.objects.create(
        name='Anim Class', teacher_name='Test Teacher',
        teacher=teacher, color='#f59e0b', icon='🎬',
    )
    return AICourse.objects.create(
        class_obj=cls, title='Algorithms', filename='algo.pdf',
        status='READY', output_dir=tmpdir, total_pages=3,
    )


class AnimationFunctionalTests(PerfTestCase):
    """Correctness tests for the concept animation endpoints."""

    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.course = make_ready_course(self.teacher, self.tmpdir)
        self.auth_student()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_request_new_animation(self):
        with patch('api.services.manim_pipeline.run_animation_in_background', return_value=None):
            res = self.client.post(
                ANIM_URL(self.course.id),
                {'concept': 'Binary Search Tree'},
                format='json',
            )
        self.assertEqual(res.status_code, 201)
        self.assertIn('animation_id', res.data)
        self.assertEqual(res.data['status'], 'PENDING')
        self.assertFalse(res.data['cached'])

    def test_request_missing_concept_returns_400(self):
        res = self.client.post(ANIM_URL(self.course.id), {}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cache_hit_ready_animation(self):
        """Second request for the same concept returns the cached READY animation."""
        existing = ConceptAnimation.objects.create(
            ai_course=self.course,
            concept='Quicksort',
            concept_key='quicksort',
            status='READY',
        )
        with patch('api.services.manim_pipeline.run_animation_in_background', return_value=None) as mock_bg:
            res = self.client.post(
                ANIM_URL(self.course.id),
                {'concept': 'Quicksort'},
                format='json',
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['cached'])
        self.assertEqual(res.data['animation_id'], existing.id)
        mock_bg.assert_not_called()

    def test_cache_hit_in_progress(self):
        existing = ConceptAnimation.objects.create(
            ai_course=self.course,
            concept='Mergesort',
            concept_key='mergesort',
            status='GENERATING',
        )
        with patch('api.services.manim_pipeline.run_animation_in_background', return_value=None) as mock_bg:
            res = self.client.post(
                ANIM_URL(self.course.id),
                {'concept': 'Mergesort'},
                format='json',
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['cached'])
        mock_bg.assert_not_called()

    def test_animation_status_pending(self):
        anim = ConceptAnimation.objects.create(
            ai_course=self.course, concept='BFS', concept_key='bfs', status='PENDING')
        res = self.client.get(STATUS_URL(anim.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'PENDING')

    def test_animation_status_ready(self):
        anim = ConceptAnimation.objects.create(
            ai_course=self.course, concept='DFS', concept_key='dfs', status='READY')
        res = self.client.get(STATUS_URL(anim.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'READY')

    def test_list_animations_empty(self):
        res = self.client.get(LIST_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

    def test_list_animations_populated(self):
        ConceptAnimation.objects.create(
            ai_course=self.course, concept='Heap', concept_key='heap', status='READY')
        ConceptAnimation.objects.create(
            ai_course=self.course, concept='Stack', concept_key='stack', status='ERROR')
        res = self.client.get(LIST_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)


class AnimationPerformanceTests(PerfTestCase):
    """Performance benchmarks for animation endpoints."""

    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.course = make_ready_course(self.teacher, self.tmpdir)
        self.anim = ConceptAnimation.objects.create(
            ai_course=self.course, concept='Dijkstra', concept_key='dijkstra',
            status='READY',
        )
        self.auth_student()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_perf_request_animation_cache_hit(self):
        """Benchmark the fast path: concept already READY → no background job."""
        url = ANIM_URL(self.course.id)
        stats = self.measure(
            lambda: self.client.post(url, {'concept': 'Dijkstra'}, format='json'),
            n=REPEAT,
        )
        self.assert_perf(stats, 'POST /api/ai-courses/<id>/animations/ (cache hit)')

    def test_perf_animation_status(self):
        url = STATUS_URL(self.anim.id)
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/animations/<id>/status/')

    def test_perf_list_animations(self):
        url = LIST_URL(self.course.id)
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/<id>/animations/list/')
