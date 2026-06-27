from django.db import models
from django.conf import settings

from .classroom import Class


class AICourse(models.Model):
    STATUS_CHOICES = [('PROCESSING', 'Processing'), ('READY', 'Ready'), ('ERROR', 'Error')]
    STEP_CHOICES = [
        ('PENDING',    'Pending'),
        ('EXTRACTING', 'Extracting PDF'),
        ('NARRATING',  'Generating narration'),
        ('TTS',        'Generating audio'),
        ('CHROMA',     'Building ChromaDB'),
        ('DONE',       'Done'),
    ]
    class_obj    = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='ai_courses')
    title        = models.CharField(max_length=300)
    filename     = models.CharField(max_length=300)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    current_step = models.CharField(max_length=20, choices=STEP_CHOICES, default='PENDING')
    total_pages  = models.IntegerField(default=0)
    error_msg    = models.TextField(blank=True)
    output_dir   = models.CharField(max_length=500)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class ConceptAnimation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATING', 'Generating code'),
        ('RENDERING', 'Rendering video'),
        ('READY', 'Ready'),
        ('ERROR', 'Error'),
    ]
    ai_course    = models.ForeignKey('AICourse', on_delete=models.CASCADE,
                                     related_name='animations')
    concept      = models.TextField()
    concept_key  = models.CharField(max_length=500)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    video_file   = models.FileField(upload_to='animations/', null=True, blank=True)
    retry_count  = models.IntegerField(default=0)
    error_msg    = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('ai_course', 'concept_key')]


class Quiz(models.Model):
    STATUS_CHOICES = [
        ('PENDING',    'Pending'),
        ('GENERATING', 'Generating'),
        ('READY',      'Ready'),
        ('ERROR',      'Error'),
    ]
    ai_course  = models.OneToOneField(
        'AICourse', on_delete=models.CASCADE, related_name='quiz'
    )
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    questions  = models.JSONField(default=list)
    error_msg  = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class QuizAttempt(models.Model):
    quiz          = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts'
    )
    answers       = models.JSONField()
    score         = models.IntegerField()
    correct_count = models.IntegerField()
    completed_at  = models.DateTimeField(auto_now_add=True)
