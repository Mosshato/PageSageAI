from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
import string

from .constants import CLASS_CODE_LENGTH


# ─── AUTH MODELS ────────────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    """
    Manager custom pentru User.
    BaseUserManager ne da utilitare de baza (make_password etc).
    Suprascriem create_user si create_superuser.
    """
    def create_user(self, email, password, role='student', **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra)
        user.set_password(password)   # hash-uieste parola cu bcrypt intern
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('role', 'teacher')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model custom care inlocuieste User-ul built-in din Django.

    AbstractBaseUser   → ne da: password (hashed), last_login, is_active
    PermissionsMixin   → ne da: is_superuser, groups, user_permissions (necesar pt admin)

    Adaugam noi: email, first_name, last_name, role, is_staff.
    """
    ROLE_CHOICES = [('student', 'Student'), ('teacher', 'Teacher')]

    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'      # folosim email in loc de username la login
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


# ─── ACADEMIC MODELS ────────────────────────────────────────────────────────

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=CLASS_CODE_LENGTH))


class Class(models.Model):
    name         = models.CharField(max_length=200)
    teacher_name = models.CharField(max_length=200)
    teacher      = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='classes')
    code         = models.CharField(max_length=10, unique=True, default=generate_code)
    color        = models.CharField(max_length=20, default='#f97316')
    icon         = models.CharField(max_length=10, default='📚')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'classes'

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    class_obj     = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrollments')
    student_email = models.EmailField()
    student_name  = models.CharField(max_length=200)
    joined_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_obj', 'student_email')


class Announcement(models.Model):
    class_obj  = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='announcements')
    title      = models.CharField(max_length=300)
    body       = models.TextField()
    pinned     = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Assignment(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('submitted', 'Submitted'), ('graded', 'Graded')]
    class_obj   = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    title       = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    due_date    = models.DateField()
    points      = models.IntegerField(default=100)
    grade       = models.IntegerField(null=True, blank=True)  # 0-100, setat de profesor la graded
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at  = models.DateTimeField(auto_now_add=True)


class AssignmentAttachment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='attachments')
    name       = models.CharField(max_length=300)
    file       = models.FileField(upload_to='attachments/assignments/', null=True, blank=True)


class Lecture(models.Model):
    class_obj   = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='lectures')
    title       = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    duration    = models.CharField(max_length=50, blank=True)
    date        = models.DateField()
    created_at  = models.DateTimeField(auto_now_add=True)


class LectureFile(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='files')
    name    = models.CharField(max_length=300)
    file    = models.FileField(upload_to='attachments/lectures/', null=True, blank=True)


class Submission(models.Model):
    assignment    = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student_email = models.EmailField()
    submitted_at  = models.DateTimeField(auto_now=True)
    grade         = models.IntegerField(null=True, blank=True)
    note          = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('assignment', 'student_email')

    def __str__(self):
        return f"{self.student_email} → {self.assignment.title}"


class SubmissionFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    name       = models.CharField(max_length=300)
    file       = models.FileField(upload_to='submissions/', null=True, blank=True)

    def __str__(self):
        return self.name


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
