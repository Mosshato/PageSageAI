from django.contrib import admin
from .domain import Class, Enrollment, Announcement, Assignment, AssignmentAttachment, Lecture, LectureFile

admin.site.register(Class)
admin.site.register(Enrollment)
admin.site.register(Announcement)
admin.site.register(Assignment)
admin.site.register(AssignmentAttachment)
admin.site.register(Lecture)
admin.site.register(LectureFile)
