import random
import string

from django.db import models
from django.conf import settings

from ..constants import CLASS_CODE_LENGTH


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
