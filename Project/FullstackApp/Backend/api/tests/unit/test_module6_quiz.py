"""
Module 6 — Quiz Performance Tests
===================================
Covers: POST teacher/classes/<id>/ai-courses/<id>/generate-quiz/
        GET  /api/ai-courses/<id>/quiz/status/
        GET  /api/ai-courses/<id>/quiz/questions/
        POST /api/ai-courses/<id>/quiz/attempt/
        GET  teacher/classes/<id>/ai-courses/<id>/quiz-results/

`run_quiz_generation_in_background` is patched so no LLM calls are made.
A pre-built READY quiz (20 MCQs, 4 options each) is used for student-facing tests.
"""
from unittest.mock import patch

from api.domain import Class, AICourse, Quiz, QuizAttempt
from api.constants import QUIZ_QUESTION_COUNT, QUIZ_OPTION_COUNT

from .base import PerfTestCase, REPEAT


def _sample_questions():
    return [
        {
            'question': f'Question {i + 1}?',
            'options':  [f'Option {j}' for j in range(QUIZ_OPTION_COUNT)],
            'correct_index': 0,
        }
        for i in range(QUIZ_QUESTION_COUNT)
    ]


def make_setup(teacher, tmpdir=''):
    cls = Class.objects.create(
        name='Quiz Class', teacher_name='Test Teacher',
        teacher=teacher, color='#ec4899', icon='📝',
    )
    course = AICourse.objects.create(
        class_obj=cls, title='OS Basics', filename='os.pdf',
        status='READY', output_dir=tmpdir or '/tmp', total_pages=10,
    )
    return cls, course


GENERATE_URL = lambda cls_id, cid: f'/api/teacher/classes/{cls_id}/ai-courses/{cid}/generate-quiz/'
STATUS_URL   = lambda cid: f'/api/ai-courses/{cid}/quiz/status/'
QUESTIONS_URL= lambda cid: f'/api/ai-courses/{cid}/quiz/questions/'
ATTEMPT_URL  = lambda cid: f'/api/ai-courses/{cid}/quiz/attempt/'
RESULTS_URL  = lambda cls_id, cid: f'/api/teacher/classes/{cls_id}/ai-courses/{cid}/quiz-results/'


class QuizFunctionalTests(PerfTestCase):
    """Correctness tests for all quiz lifecycle endpoints."""

    def setUp(self):
        super().setUp()
        self.cls, self.course = make_setup(self.teacher)

    # ── Generation ──────────────────────────────────────────────────────────

    def test_generate_quiz_creates_pending(self):
        self.auth_teacher()
        with patch('api.services.quiz_pipeline.run_quiz_generation_in_background', return_value=None):
            res = self.client.post(GENERATE_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['status'], 'PENDING')

    def test_generate_quiz_not_ready_course_returns_400(self):
        self.auth_teacher()
        self.course.status = 'PROCESSING'
        self.course.save()
        res = self.client.post(GENERATE_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 400)

    def test_generate_quiz_already_ready_returns_existing(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_teacher()
        res = self.client.post(GENERATE_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'READY')

    def test_generate_quiz_wrong_teacher_returns_403(self):
        self.auth_student()
        res = self.client.post(GENERATE_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 403)

    # ── Status ──────────────────────────────────────────────────────────────

    def test_quiz_status_not_generated(self):
        self.auth_student()
        res = self.client.get(STATUS_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'NOT_GENERATED')

    def test_quiz_status_pending(self):
        Quiz.objects.create(ai_course=self.course, status='PENDING', questions=[])
        self.auth_student()
        res = self.client.get(STATUS_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'PENDING')

    def test_quiz_status_ready(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        res = self.client.get(STATUS_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'READY')
        self.assertEqual(res.data['question_count'], QUIZ_QUESTION_COUNT)

    # ── Questions ────────────────────────────────────────────────────────────

    def test_get_questions_strips_correct_index(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        res = self.client.get(QUESTIONS_URL(self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['questions']), QUIZ_QUESTION_COUNT)
        for q in res.data['questions']:
            self.assertNotIn('correct_index', q)   # answer hidden from students

    def test_get_questions_not_ready_returns_404(self):
        Quiz.objects.create(ai_course=self.course, status='GENERATING', questions=[])
        self.auth_student()
        res = self.client.get(QUESTIONS_URL(self.course.id))
        self.assertEqual(res.status_code, 404)

    # ── Attempt ──────────────────────────────────────────────────────────────

    def test_submit_perfect_score(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        answers = [0] * QUIZ_QUESTION_COUNT
        res = self.client.post(ATTEMPT_URL(self.course.id),
                               {'answers': answers}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['score'], 100)
        self.assertEqual(res.data['correct_count'], QUIZ_QUESTION_COUNT)

    def test_submit_zero_score(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        answers = [1] * QUIZ_QUESTION_COUNT
        res = self.client.post(ATTEMPT_URL(self.course.id),
                               {'answers': answers}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['score'], 0)

    def test_submit_wrong_answer_count_returns_400(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        res = self.client.post(ATTEMPT_URL(self.course.id),
                               {'answers': [0, 1]}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_submit_out_of_range_index_returns_400(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_student()
        answers = [QUIZ_OPTION_COUNT] * QUIZ_QUESTION_COUNT   # index == option count → invalid
        res = self.client.post(ATTEMPT_URL(self.course.id),
                               {'answers': answers}, format='json')
        self.assertEqual(res.status_code, 400)

    # ── Teacher results ───────────────────────────────────────────────────────

    def test_teacher_results_no_attempts(self):
        Quiz.objects.create(ai_course=self.course, status='READY',
                            questions=_sample_questions())
        self.auth_teacher()
        res = self.client.get(RESULTS_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['attempts'], [])

    def test_teacher_results_with_attempts(self):
        quiz = Quiz.objects.create(ai_course=self.course, status='READY',
                                   questions=_sample_questions())
        QuizAttempt.objects.create(
            quiz=quiz, student=self.student,
            answers=[0] * QUIZ_QUESTION_COUNT,
            score=100, correct_count=QUIZ_QUESTION_COUNT,
        )
        self.auth_teacher()
        res = self.client.get(RESULTS_URL(self.cls.id, self.course.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['attempts']), 1)
        self.assertEqual(res.data['attempts'][0]['score'], 100)


class QuizPerformanceTests(PerfTestCase):
    """Performance benchmarks for all quiz endpoints."""

    def setUp(self):
        super().setUp()
        self.cls, self.course = make_setup(self.teacher)
        self.quiz = Quiz.objects.create(
            ai_course=self.course, status='READY',
            questions=_sample_questions(),
        )

    def test_perf_quiz_status(self):
        self.auth_student()
        url = STATUS_URL(self.course.id)
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/<id>/quiz/status/')

    def test_perf_quiz_questions(self):
        self.auth_student()
        url = QUESTIONS_URL(self.course.id)
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/<id>/quiz/questions/')

    def test_perf_submit_attempt(self):
        self.auth_student()
        url = ATTEMPT_URL(self.course.id)
        answers = [0] * QUIZ_QUESTION_COUNT
        stats = self.measure(
            lambda: self.client.post(url, {'answers': answers}, format='json'),
            n=REPEAT,
        )
        self.assert_perf(stats, 'POST /api/ai-courses/<id>/quiz/attempt/')

    def test_perf_teacher_results(self):
        self.auth_teacher()
        url = RESULTS_URL(self.cls.id, self.course.id)
        stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  teacher/ai-courses/<id>/quiz-results/')
