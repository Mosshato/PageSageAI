"""
Module 3 — PDF Ingestion & Narration Generation Performance Tests
=================================================================
Covers: POST teacher/classes/<id>/ai-courses/ (PDF upload → pipeline start),
        GET  ai-courses/<id>/status/,
        GET  ai-courses/<id>/page/<n>/,
        DELETE teacher/classes/<id>/ai-courses/<id>/

The actual AI pipeline (ingest_pdf, narrate_course, TTS) is mocked so tests
run without GPU/API resources.  The file-system layer that saves the uploaded
PDF is also patched to a temporary directory.
"""
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from api.models import Class, AICourse

from .base import PerfTestCase, REPEAT


def make_class(teacher):
    return Class.objects.create(
        name='AI Class', teacher_name='Test Teacher',
        teacher=teacher, color='#10b981', icon='🤖',
    )


class PDFPipelineFunctionalTests(PerfTestCase):
    """
    Correctness tests for PDF-upload and status endpoints.
    `run_pipeline_in_background` is patched so no real AI processing runs.
    """

    def setUp(self):
        super().setUp()
        self.cls = make_class(self.teacher)
        self.tmpdir = tempfile.mkdtemp()
        # Structure: tmpdir/media/ai_courses/ so relative_to(MEDIA_ROOT) works
        self.media_root = Path(self.tmpdir) / 'media'
        self.ai_root = self.media_root / 'ai_courses'
        self.ai_root.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def _upload_pdf(self):
        pdf = SimpleUploadedFile('lecture.pdf', b'%PDF-1.4 dummy', content_type='application/pdf')
        url = f'/api/teacher/classes/{self.cls.id}/ai-courses/'
        with override_settings(MEDIA_ROOT=str(self.media_root)), \
             patch('api.views.ai_views.AI_COURSES_ROOT', self.ai_root), \
             patch('api.services.ai_pipeline.run_pipeline_in_background', return_value=None):
            return self.client.post(url, {'file': pdf, 'title': 'Lecture 1'}, format='multipart')

    def test_upload_returns_201(self):
        self.auth_teacher()
        res = self._upload_pdf()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['status'], 'PROCESSING')
        self.assertEqual(res.data['title'], 'Lecture 1')

    def test_upload_without_file_returns_400(self):
        self.auth_teacher()
        url = f'/api/teacher/classes/{self.cls.id}/ai-courses/'
        res = self.client.post(url, {'title': 'No file'}, format='multipart')
        self.assertEqual(res.status_code, 400)

    def test_upload_wrong_teacher_returns_404(self):
        self.auth_student()
        url = f'/api/teacher/classes/{self.cls.id}/ai-courses/'
        pdf = SimpleUploadedFile('x.pdf', b'%PDF', content_type='application/pdf')
        res = self.client.post(url, {'file': pdf}, format='multipart')
        self.assertEqual(res.status_code, 404)

    def test_status_processing(self):
        self.auth_teacher()
        self._upload_pdf()
        course = AICourse.objects.filter(class_obj=self.cls).first()
        with override_settings(MEDIA_ROOT=str(self.media_root)):
            res = self.client.get(f'/api/ai-courses/{course.id}/status/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('status', res.data)

    def test_page_not_ready_returns_400(self):
        self.auth_teacher()
        course = AICourse.objects.create(
            class_obj=self.cls, title='X', filename='x.pdf',
            status='PROCESSING', output_dir=str(self.ai_root),
        )
        res = self.client.get(f'/api/ai-courses/{course.id}/page/1/')
        self.assertEqual(res.status_code, 400)

    def test_page_ready_returns_urls(self):
        """Create a READY course with a dummy PNG on disk; endpoint must return image_url."""
        out = self.ai_root / 'ready_page'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'page_0001.png').write_bytes(b'\x89PNG fake')
        course = AICourse.objects.create(
            class_obj=self.cls, title='Ready Course', filename='r.pdf',
            status='READY', output_dir=str(out), total_pages=1,
        )
        self.auth_student()
        with override_settings(MEDIA_ROOT=str(self.media_root)), \
             patch('api.views.ai_views.AI_COURSES_ROOT', self.ai_root):
            res = self.client.get(f'/api/ai-courses/{course.id}/page/1/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('image_url', res.data)

    def test_delete_course(self):
        self.auth_teacher()
        course = AICourse.objects.create(
            class_obj=self.cls, title='Del', filename='del.pdf',
            status='PROCESSING', output_dir=str(self.ai_root),
        )
        url = f'/api/teacher/classes/{self.cls.id}/ai-courses/{course.id}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(AICourse.objects.filter(id=course.id).exists())


class PDFPipelinePerformanceTests(PerfTestCase):
    """Performance benchmarks: upload API layer + DB write, no actual pipeline."""

    def setUp(self):
        super().setUp()
        self.cls = make_class(self.teacher)
        self.tmpdir = tempfile.mkdtemp()
        self.media_root = Path(self.tmpdir) / 'media'
        self.ai_root = self.media_root / 'ai_courses'
        self.ai_root.mkdir(parents=True)
        # Pre-create a READY course for status/page polling benchmarks
        out = self.ai_root / 'ready'
        out.mkdir()
        (out / 'page_0001.png').write_bytes(b'\x89PNG fake')
        self.course = AICourse.objects.create(
            class_obj=self.cls, title='Perf Course', filename='perf.pdf',
            status='READY', output_dir=str(out), total_pages=1,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_perf_upload(self):
        self.auth_teacher()
        counter = [0]

        def do_upload():
            counter[0] += 1
            pdf = SimpleUploadedFile(f'f{counter[0]}.pdf', b'%PDF', content_type='application/pdf')
            url = f'/api/teacher/classes/{self.cls.id}/ai-courses/'
            with override_settings(MEDIA_ROOT=str(self.media_root)), \
                 patch('api.views.ai_views.AI_COURSES_ROOT', self.ai_root), \
                 patch('api.services.ai_pipeline.run_pipeline_in_background', return_value=None):
                self.client.post(url, {'file': pdf}, format='multipart')

        stats = self.measure(do_upload, n=REPEAT)
        self.assert_perf(stats, 'POST /api/teacher/classes/<id>/ai-courses/ (upload)')

    def test_perf_status(self):
        self.auth_teacher()
        url = f'/api/ai-courses/{self.course.id}/status/'
        with override_settings(MEDIA_ROOT=str(self.media_root)):
            stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/<id>/status/')

    def test_perf_page(self):
        self.auth_student()
        url = f'/api/ai-courses/{self.course.id}/page/1/'
        with override_settings(MEDIA_ROOT=str(self.media_root)):
            stats = self.measure(lambda: self.client.get(url), n=REPEAT)
        self.assert_perf(stats, 'GET  /api/ai-courses/<id>/page/<n>/')
