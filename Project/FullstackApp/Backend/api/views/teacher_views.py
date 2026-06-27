from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from ..models import Class, Enrollment, Assignment, Submission, Announcement, Lecture, LectureFile, AssignmentAttachment
from ..serializers import TeacherClassSerializer, TeacherClassDetailSerializer, TeacherSubmissionSerializer
from ..constants import MIN_GRADE, MAX_GRADE


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_students(request):
    classes = Class.objects.filter(teacher=request.user).prefetch_related('enrollments')
    seen = {}
    for cls in classes:
        for enr in cls.enrollments.all():
            if enr.student_email not in seen:
                seen[enr.student_email] = {
                    'email': enr.student_email,
                    'name':  enr.student_name,
                    'classes': [],
                }
            seen[enr.student_email]['classes'].append({
                'id':    cls.id,
                'name':  cls.name,
                'color': cls.color,
                'icon':  cls.icon,
            })
    return Response(list(seen.values()))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_class_list(request):
    if request.method == 'GET':
        classes = Class.objects.filter(teacher=request.user).prefetch_related('enrollments', 'assignments__submissions')
        return Response(TeacherClassSerializer(classes, many=True).data)

    # POST — create a new class
    name         = request.data.get('name', '').strip()
    teacher_name = request.data.get('teacher_name', '').strip()
    color        = request.data.get('color', '#f97316').strip()
    icon         = request.data.get('icon', '📚').strip()

    if not name:
        return Response({'error': 'Class name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not teacher_name:
        teacher_name = f"{request.user.first_name} {request.user.last_name}".strip()

    cls = Class.objects.create(
        name=name, teacher_name=teacher_name,
        teacher=request.user, color=color, icon=icon,
    )
    return Response(TeacherClassSerializer(cls).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_stats(request):
    classes = Class.objects.filter(teacher=request.user).prefetch_related('enrollments')
    total_classes   = classes.count()
    unique_emails   = Enrollment.objects.filter(class_obj__teacher=request.user).values('student_email').distinct().count()
    total_assignments = Assignment.objects.filter(class_obj__teacher=request.user).count()
    total_submissions = Submission.objects.filter(assignment__class_obj__teacher=request.user).count()
    awaiting_grades   = Submission.objects.filter(
        assignment__class_obj__teacher=request.user,
        grade__isnull=True,
    ).count()
    return Response({
        'total_classes':      total_classes,
        'total_students':     unique_emails,
        'total_assignments':  total_assignments,
        'total_submissions':  total_submissions,
        'awaiting_grades':    awaiting_grades,
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_class_detail(request, class_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TeacherClassDetailSerializer(cls).data)

    if request.method == 'PATCH':
        for field in ('name', 'teacher_name', 'color', 'icon'):
            val = request.data.get(field)
            if val is not None:
                setattr(cls, field, val)
        cls.save()
        return Response(TeacherClassSerializer(cls).data)

    # DELETE
    cls.delete()
    return Response({'message': 'Class deleted.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_student(request, class_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    try:
        u = User.objects.get(email=email)
        name = f"{u.first_name} {u.last_name}".strip() or email
    except User.DoesNotExist:
        return Response({'error': 'No account found with that email.'}, status=status.HTTP_404_NOT_FOUND)

    if Enrollment.objects.filter(class_obj=cls, student_email=email).exists():
        return Response({'error': 'Student already enrolled.'}, status=status.HTTP_400_BAD_REQUEST)

    enrollment = Enrollment.objects.create(class_obj=cls, student_email=email, student_name=name)
    from ..serializers import EnrollmentSerializer  # noqa: local import avoids circular
    return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_remove_student(request, class_id, enrollment_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        enrollment = Enrollment.objects.get(id=enrollment_id, class_obj=cls)
    except (Class.DoesNotExist, Enrollment.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    enrollment.delete()
    return Response({'message': 'Student removed.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_announcement(request, class_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    title  = request.data.get('title', '').strip()
    body   = request.data.get('body', '').strip()
    pinned = request.data.get('pinned', False)
    if not title or not body:
        return Response({'error': 'Title and body are required.'}, status=status.HTTP_400_BAD_REQUEST)

    ann = Announcement.objects.create(class_obj=cls, title=title, body=body, pinned=pinned)
    from ..serializers import AnnouncementSerializer
    return Response(AnnouncementSerializer(ann).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_announcement(request, class_id, announcement_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        ann = Announcement.objects.get(id=announcement_id, class_obj=cls)
    except (Class.DoesNotExist, Announcement.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    ann.delete()
    return Response({'message': 'Announcement deleted.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_assignment(request, class_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    title       = request.data.get('title', '').strip()
    description = request.data.get('description', '').strip()
    due_date    = request.data.get('due_date', '')
    points      = request.data.get('points', 100)

    if not title or not due_date:
        return Response({'error': 'Title and due_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

    assignment = Assignment.objects.create(
        class_obj=cls, title=title, description=description,
        due_date=due_date, points=points, status='pending',
    )
    for f in request.FILES.getlist('files'):
        AssignmentAttachment.objects.create(assignment=assignment, name=f.name, file=f)

    from ..serializers import TeacherAssignmentSerializer
    return Response(TeacherAssignmentSerializer(assignment, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def teacher_edit_assignment(request, class_id, assignment_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        assignment = Assignment.objects.get(id=assignment_id, class_obj=cls)
    except (Class.DoesNotExist, Assignment.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    for field in ('title', 'description', 'due_date', 'points'):
        val = request.data.get(field)
        if val is not None:
            setattr(assignment, field, val)
    assignment.save()

    # Keep only selected existing attachments, add new uploaded files
    keep_ids_raw = request.data.getlist('keep_ids') if hasattr(request.data, 'getlist') else request.data.get('keep_ids', [])
    keep_ids = [int(x) for x in keep_ids_raw if x]
    assignment.attachments.exclude(id__in=keep_ids).delete()
    for f in request.FILES.getlist('files'):
        AssignmentAttachment.objects.create(assignment=assignment, name=f.name, file=f)

    from ..serializers import TeacherAssignmentSerializer
    return Response(TeacherAssignmentSerializer(assignment, context={'request': request}).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_assignment(request, class_id, assignment_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        assignment = Assignment.objects.get(id=assignment_id, class_obj=cls)
    except (Class.DoesNotExist, Assignment.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    assignment.delete()
    return Response({'message': 'Assignment deleted.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_add_lecture(request, class_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    title       = request.data.get('title', '').strip()
    description = request.data.get('description', '').strip()
    duration    = request.data.get('duration', '').strip()
    date        = request.data.get('date', '')

    if not title or not date:
        return Response({'error': 'Title and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

    lecture = Lecture.objects.create(class_obj=cls, title=title, description=description, duration=duration, date=date)
    for f in request.FILES.getlist('files'):
        LectureFile.objects.create(lecture=lecture, name=f.name, file=f)

    from ..serializers import LectureSerializer
    return Response(LectureSerializer(lecture, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_lecture(request, class_id, lecture_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        lecture = Lecture.objects.get(id=lecture_id, class_obj=cls)
    except (Class.DoesNotExist, Lecture.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    lecture.delete()
    return Response({'message': 'Lecture deleted.'}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def teacher_grade_submission(request, class_id, submission_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        submission = Submission.objects.get(id=submission_id, assignment__class_obj=cls)
    except (Class.DoesNotExist, Submission.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    grade = request.data.get('grade')
    note  = request.data.get('note', submission.note)

    if grade is not None:
        try:
            grade = int(grade)
            if not MIN_GRADE <= grade <= MAX_GRADE:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': f'Grade must be {MIN_GRADE}–{MAX_GRADE}.'}, status=status.HTTP_400_BAD_REQUEST)
        submission.grade = grade
        submission.assignment.status = 'graded'
        submission.assignment.save()

    submission.note = note
    submission.save()
    return Response(TeacherSubmissionSerializer(submission).data)
