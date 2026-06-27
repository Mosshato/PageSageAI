from django.db import models

from .classroom import Class


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
