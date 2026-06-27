from django.db import models

from .classroom import Class


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
