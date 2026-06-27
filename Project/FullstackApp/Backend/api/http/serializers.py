from rest_framework import serializers
from ..domain import Class, Enrollment, Announcement, Assignment, AssignmentAttachment, Lecture, LectureFile, Submission, SubmissionFile
from django.db.models import Count


class AssignmentAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    class Meta:
        model = AssignmentAttachment
        fields = ['id', 'name', 'url']


class SubmissionFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    class Meta:
        model = SubmissionFile
        fields = ['id', 'name', 'url']


class SubmissionSerializer(serializers.ModelSerializer):
    files = SubmissionFileSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = ['id', 'submitted_at', 'files', 'grade', 'note']


class TeacherSubmissionSerializer(serializers.ModelSerializer):
    files        = SubmissionFileSerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()

    def get_student_name(self, obj):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            u = User.objects.get(email=obj.student_email)
            name = f"{u.first_name} {u.last_name}".strip()
            if name:
                return name
        except User.DoesNotExist:
            pass
        enr = Enrollment.objects.filter(
            class_obj=obj.assignment.class_obj,
            student_email=obj.student_email,
        ).first()
        return enr.student_name if enr else obj.student_email

    class Meta:
        model = Submission
        fields = ['id', 'student_email', 'student_name', 'submitted_at', 'files', 'grade', 'note']


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    attachments = AssignmentAttachmentSerializer(many=True, read_only=True)
    submissions = TeacherSubmissionSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'points', 'status', 'attachments', 'submissions']


class AssignmentSerializer(serializers.ModelSerializer):
    attachments    = AssignmentAttachmentSerializer(many=True, read_only=True)
    class_name     = serializers.CharField(source='class_obj.name', read_only=True)
    class_color    = serializers.CharField(source='class_obj.color', read_only=True)
    # my_submission is injected by the view via context — None if not submitted
    my_submission  = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'points', 'grade',
                  'status', 'attachments', 'class_name', 'class_color', 'class_obj',
                  'my_submission']

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        sub = obj.submissions.filter(student_email=request.user.email).first()
        if sub is None:
            return None
        return SubmissionSerializer(sub, context={'request': request}).data


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'body', 'pinned', 'created_at']


class LectureFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    class Meta:
        model = LectureFile
        fields = ['id', 'name', 'url']


class LectureSerializer(serializers.ModelSerializer):
    files = LectureFileSerializer(many=True, read_only=True)

    class Meta:
        model = Lecture
        fields = ['id', 'title', 'description', 'duration', 'date', 'files']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student_email', 'student_name', 'joined_at']


class ClassSerializer(serializers.ModelSerializer):
    pending_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'teacher_name', 'code', 'color', 'icon', 'pending_count']

    def get_pending_count(self, obj):
        # Assignments that exist and have no submission from this student
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        submitted_ids = Submission.objects.filter(
            assignment__class_obj=obj,
            student_email=request.user.email,
        ).values_list('assignment_id', flat=True)
        return obj.assignments.filter(status='pending').exclude(id__in=submitted_ids).count()


class TeacherClassSerializer(serializers.ModelSerializer):
    student_count   = serializers.SerializerMethodField()
    awaiting_grades = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'teacher_name', 'code', 'color', 'icon', 'student_count', 'awaiting_grades']

    def get_student_count(self, obj):
        return obj.enrollments.count()

    def get_awaiting_grades(self, obj):
        return Submission.objects.filter(
            assignment__class_obj=obj,
            assignment__status='submitted',
        ).count()


class TeacherClassDetailSerializer(serializers.ModelSerializer):
    announcements = AnnouncementSerializer(many=True, read_only=True)
    assignments   = TeacherAssignmentSerializer(many=True, read_only=True)
    lectures      = LectureSerializer(many=True, read_only=True)
    enrollments   = EnrollmentSerializer(many=True, read_only=True)

    class Meta:
        model = Class
        fields = ['id', 'name', 'teacher_name', 'code', 'color', 'icon',
                  'announcements', 'assignments', 'lectures', 'enrollments']


class ClassDetailSerializer(serializers.ModelSerializer):
    announcements = AnnouncementSerializer(many=True, read_only=True)
    assignments   = serializers.SerializerMethodField()
    lectures      = LectureSerializer(many=True, read_only=True)
    classmates    = EnrollmentSerializer(many=True, source='enrollments', read_only=True)

    class Meta:
        model = Class
        fields = ['id', 'name', 'teacher_name', 'code', 'color', 'icon',
                  'announcements', 'assignments', 'lectures', 'classmates']

    def get_assignments(self, obj):
        request = self.context.get('request')
        return AssignmentSerializer(
            obj.assignments.prefetch_related('attachments', 'submissions'),
            many=True,
            context={'request': request},
        ).data
