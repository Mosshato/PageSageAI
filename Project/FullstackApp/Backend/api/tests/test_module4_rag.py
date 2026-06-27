"""
Module 4 — RAG Indexing, Query & ChromaDB Seeding Performance Tests
====================================================================
Covers: POST /api/ai-courses/<id>/ask/
        POST /api/ai-courses/<id>/reformulate/
        GET  /api/ai-courses/class/<id>/

`query_rag` (which talks to ChromaDB + Gemini) is patched with a fast mock
so the benchmark isolates the Django/DRF request-handling layer only.
"""
import tempfile
import shutil
from unittest.mock import patch

from api.models import Class, AICourse

from .base import PerfTestCase, REPEAT

RAG_MOCK_ANSWER = (
    'The concept of a stack follows LIFO (Last In, First Out) ordering. '
    'Elements are added and removed from the same end, called the top.'
)


def make_ready_course(teacher, tmpdir):
    cls = Class.objects.create(
        name='RAG Class', teacher_name='Test Teacher',
        teacher=teacher, color='#6366f1', icon='🔍',
    )
    return AICourse.objects.create(
        class_obj=cls, title='Data Structures', filename='ds.pdf',
        status='READY', output_dir=tmpdir, total_pages=5,
    )


class RAGFunctionalTests(PerfTestCase):
    """Correctness: ask and reformulate endpoints with mocked query_rag."""

    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.course = make_ready_course(self.teacher, self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_ask_valid_question(self):
        self.auth_student()
        with patch('api.services.ai_pipeline.query_rag', return_value=RAG_MOCK_ANSWER):
            res = self.client.post(
                f'/api/ai-courses/{self.course.id}/ask/',
                {'question': 'What is a stack?'}, format='json',
            )
        self.assertEqual(res.status_code, 200)
        self.assertIn('answer', res.data)
        self.assertEqual(res.data['answer'], RAG_MOCK_ANSWER)

    def test_ask_missing_question_returns_400(self):
        self.auth_student()
        res = self.client.post(
            f'/api/ai-courses/{self.course.id}/ask/',
            {}, format='json',
        )
        self.assertEqual(res.status_code, 400)

    def test_ask_nonexistent_course_returns_404(self):
        self.auth_student()
        res = self.client.post('/api/ai-courses/99999/ask/',
                               {'question': 'test'}, format='json')
        self.assertEqual(res.status_code, 404)

    def test_reformulate_valid(self):
        self.auth_student()
        with patch('api.services.ai_pipeline.query_rag', return_value='Simpler: LIFO means last added, first removed.'):
            res = self.client.post(
                f'/api/ai-courses/{self.course.id}/reformulate/',
                {'question': 'What is a stack?',
                 'previous_answer': RAG_MOCK_ANSWER},
                format='json',
            )
        self.assertEqual(res.status_code, 200)
        self.assertIn('answer', res.data)

    def test_reformulate_missing_question_returns_400(self):
        self.auth_student()
        res = self.client.post(
            f'/api/ai-courses/{self.course.id}/reformulate/',
            {'previous_answer': RAG_MOCK_ANSWER}, format='json',
        )
        self.assertEqual(res.status_code, 400)

    def test_list_courses_for_class(self):
        self.auth_student()
        res = self.client.get(f'/api/ai-courses/class/{self.course.class_obj_id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], self.course.id)

    def test_ask_propagates_rag_error(self):
        self.auth_student()
        with patch('api.services.ai_pipeline.query_rag', side_effect=RuntimeError('ChromaDB unavailable')):
            res = self.client.post(
                f'/api/ai-courses/{self.course.id}/ask/',
                {'question': 'test'}, format='json',
            )
        self.assertEqual(res.status_code, 500)


class RAGPerformanceTests(PerfTestCase):
    """Performance benchmarks for RAG endpoints (query_rag mocked to isolate DRF layer)."""

    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.course = make_ready_course(self.teacher, self.tmpdir)
        self.auth_student()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_perf_ask(self):
        url = f'/api/ai-courses/{self.course.id}/ask/'
        with patch('api.services.ai_pipeline.query_rag', return_value=RAG_MOCK_ANSWER):
            stats = self.measure(
                lambda: self.client.post(url, {'question': 'What is a queue?'}, format='json'),
                n=REPEAT,
            )
        self.assert_perf(stats, 'POST /api/ai-courses/<id>/ask/')

    def test_perf_reformulate(self):
        url = f'/api/ai-courses/{self.course.id}/reformulate/'
        with patch('api.services.ai_pipeline.query_rag', return_value='Simpler answer.'):
            stats = self.measure(
                lambda: self.client.post(url,
                    {'question': 'Explain', 'previous_answer': 'Long answer...'},
                    format='json'),
                n=REPEAT,
            )
        self.assert_perf(stats, 'POST /api/ai-courses/<id>/reformulate/')

    def test_perf_list_courses(self):
        url = f'/api/ai-courses/class/{self.course.class_obj_id}/'
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/class/<id>/')
