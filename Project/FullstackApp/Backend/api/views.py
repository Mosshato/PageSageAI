import json
from pathlib import Path

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Class, Enrollment, Assignment, Submission, SubmissionFile, Announcement, Lecture, LectureFile, AssignmentAttachment, AICourse, ConceptAnimation, Quiz, QuizAttempt
from .serializers import (ClassSerializer, ClassDetailSerializer, AssignmentSerializer,
                          SubmissionSerializer, TeacherClassSerializer,
                          TeacherClassDetailSerializer, TeacherSubmissionSerializer)
from .constants import MIN_GRADE, MAX_GRADE, QUIZ_QUESTION_COUNT, QUIZ_OPTION_COUNT


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_list(request):
    enrolled_ids = Enrollment.objects.filter(
        student_email=request.user.email
    ).values_list('class_obj_id', flat=True)
    classes = Class.objects.filter(id__in=enrolled_ids).prefetch_related('assignments')
    serializer = ClassSerializer(classes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll(request):
    code = request.data.get('code', '').strip().upper()
    if not code:
        return Response({'error': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cls = Class.objects.get(code=code)
    except Class.DoesNotExist:
        return Response({'error': 'Class not found. Check the code and try again.'}, status=status.HTTP_404_NOT_FOUND)

    student_email = request.user.email
    student_name  = f"{request.user.first_name} {request.user.last_name}".strip()

    enrollment, created = Enrollment.objects.get_or_create(
        class_obj=cls, student_email=student_email,
        defaults={'student_name': student_name},
    )
    if not created:
        return Response({'error': 'You are already enrolled in this class.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(ClassSerializer(cls, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_detail(request, class_id):
    try:
        cls = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(ClassDetailSerializer(cls, context={'request': request}).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def quit_class(request, class_id):
    try:
        enrollment = Enrollment.objects.get(
            class_obj_id=class_id,
            student_email=request.user.email,
        )
    except Enrollment.DoesNotExist:
        return Response({'error': 'You are not enrolled in this class.'}, status=status.HTTP_404_NOT_FOUND)
    enrollment.delete()
    return Response({'message': 'Successfully left the class.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_assignments(request):
    enrolled_ids = Enrollment.objects.filter(
        student_email=request.user.email
    ).values_list('class_obj_id', flat=True)
    assignments = Assignment.objects.filter(
        class_obj_id__in=enrolled_ids
    ).select_related('class_obj').prefetch_related('attachments', 'submissions')
    return Response(AssignmentSerializer(assignments, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_assignment(request, assignment_id):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return Response({'error': 'Assignment not found.'}, status=status.HTTP_404_NOT_FOUND)

    uploaded = request.FILES.getlist('files')
    if not uploaded:
        return Response({'error': 'At least one file is required.'}, status=status.HTTP_400_BAD_REQUEST)

    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student_email=request.user.email,
    )
    if not created:
        # Resubmit — clear previous grade/note and reset assignment status
        submission.grade = None
        submission.note = ''
        if assignment.status == 'graded':
            assignment.status = 'submitted'
            assignment.save()

    submission.files.all().delete()
    for f in uploaded:
        SubmissionFile.objects.create(submission=submission, name=f.name, file=f)
    submission.save()

    return Response(SubmissionSerializer(submission, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsubmit_assignment(request, assignment_id):
    """
    DELETE /api/assignments/:id/submit/
    Sterge complet submission-ul studentului.
    """
    try:
        submission = Submission.objects.get(
            assignment_id=assignment_id,
            student_email=request.user.email,
        )
    except Submission.DoesNotExist:
        return Response({'error': 'No submission found.'}, status=status.HTTP_404_NOT_FOUND)

    assignment = submission.assignment
    submission.delete()
    if assignment.status in ('submitted', 'graded'):
        assignment.status = 'pending'
        assignment.save()
    return Response({'message': 'Submission removed.'}, status=status.HTTP_200_OK)


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
    from .serializers import EnrollmentSerializer  # noqa: local import avoids circular
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
    from .serializers import AnnouncementSerializer
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

    from .serializers import TeacherAssignmentSerializer
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

    from .serializers import TeacherAssignmentSerializer
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

    from .serializers import LectureSerializer
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_stats(request):
    email = request.user.email
    enrolled_ids = list(Enrollment.objects.filter(
        student_email=email
    ).values_list('class_obj_id', flat=True))

    if not enrolled_ids:
        return Response({
            'empty': True,
            'message': 'You are not enrolled in any class yet.',
            'classes_count': 0,
            'assignments_completed': 0,
            'assignments_pending': 0,
            'assignments_total': 0,
            'avg_grade': None,
            'grades_per_class': [],
        })

    assignments = Assignment.objects.filter(class_obj_id__in=enrolled_ids)
    total = assignments.count()

    my_subs = Submission.objects.filter(
        student_email=email,
        assignment__class_obj_id__in=enrolled_ids,
    )
    submitted_ids = set(my_subs.values_list('assignment_id', flat=True))

    completed = my_subs.count()
    pending   = assignments.filter(status='pending').exclude(id__in=submitted_ids).count()

    graded_subs = my_subs.filter(grade__isnull=False)
    avg_result  = graded_subs.aggregate(avg=Avg('grade'))
    avg_grade   = round(avg_result['avg'], 1) if avg_result['avg'] is not None else None

    classes = Class.objects.filter(id__in=enrolled_ids)
    grades_per_class = []
    for cls in classes:
        cls_subs  = my_subs.filter(assignment__class_obj=cls, grade__isnull=False)
        cls_avg   = cls_subs.aggregate(avg=Avg('grade'))['avg']
        grades_per_class.append({
            'class_id':     cls.id,
            'class_name':   cls.name,
            'color':        cls.color,
            'icon':         cls.icon,
            'avg_grade':    round(cls_avg, 1) if cls_avg is not None else None,
            'graded_count': cls_subs.count(),
        })

    return Response({
        'empty':                 False,
        'classes_count':         len(enrolled_ids),
        'assignments_total':     total,
        'assignments_completed': completed,
        'assignments_pending':   pending,
        'avg_grade':             avg_grade,
        'grades_per_class':      grades_per_class,
    })


# ── AI Teaching Endpoints ─────────────────────────────────────────────────────

AI_COURSES_ROOT = Path(settings.MEDIA_ROOT) / "ai_courses"


def _ai_course_data(course):
    pdf_url = None
    if course.output_dir and course.filename:
        pdf_path = Path(course.output_dir) / course.filename
        if pdf_path.exists():
            rel = pdf_path.relative_to(settings.MEDIA_ROOT)
            pdf_url = f"{settings.MEDIA_URL}{rel.as_posix()}"
    return {
        'id':          course.id,
        'title':       course.title,
        'filename':    course.filename,
        'status':      course.status,
        'total_pages': course.total_pages,
        'error_msg':   course.error_msg,
        'created_at':  course.created_at.isoformat(),
        'pdf_url':     pdf_url,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_upload_ai_course(request, class_id):
    """Upload a PDF; start background AI processing pipeline."""
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
    except Class.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    pdf_file = request.FILES.get('file')
    title    = request.data.get('title', '').strip() or (pdf_file.name if pdf_file else 'Untitled')

    if not pdf_file:
        return Response({'error': 'file is required.'}, status=status.HTTP_400_BAD_REQUEST)

    course = AICourse.objects.create(
        class_obj=cls,
        title=title,
        filename=pdf_file.name,
        status='PROCESSING',
        output_dir='',
    )

    output_dir = AI_COURSES_ROOT / str(course.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / pdf_file.name
    with open(pdf_path, 'wb') as f:
        for chunk in pdf_file.chunks():
            f.write(chunk)

    course.output_dir = str(output_dir)
    course.save()

    from .ai_pipeline import run_pipeline_in_background
    run_pipeline_in_background(course.id, pdf_path, output_dir)

    return Response(_ai_course_data(course), status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def teacher_delete_ai_course(request, class_id, course_id):
    try:
        cls = Class.objects.get(id=class_id, teacher=request.user)
        course = AICourse.objects.get(id=course_id, class_obj=cls)
    except (Class.DoesNotExist, AICourse.DoesNotExist):
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    import shutil
    if course.output_dir:
        import pathlib
        out = pathlib.Path(course.output_dir)
        if out.exists():
            shutil.rmtree(out, ignore_errors=True)

    course.delete()
    return Response({'message': 'AI course deleted.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_course_status(request, course_id):
    try:
        course = AICourse.objects.get(id=course_id)
    except AICourse.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_ai_course_data(course))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_courses_for_class(request, class_id):
    courses = AICourse.objects.filter(class_obj_id=class_id).order_by('-created_at')
    return Response([_ai_course_data(c) for c in courses])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_course_page(request, course_id, page_number):
    try:
        course = AICourse.objects.get(id=course_id)
    except AICourse.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if course.status != 'READY':
        return Response({'error': 'Course is not ready yet.'}, status=status.HTTP_400_BAD_REQUEST)

    output_dir = Path(course.output_dir)
    png_name   = f"page_{page_number:04d}.png"
    mp3_name   = f"page_{page_number:04d}.mp3"
    png_path   = output_dir / png_name
    mp3_path   = output_dir / "audio" / mp3_name

    if not png_path.exists():
        return Response({'error': 'Page not found.'}, status=status.HTTP_404_NOT_FOUND)

    media_prefix = request.build_absolute_uri(settings.MEDIA_URL)
    rel_base     = f"ai_courses/{course_id}"

    return Response({
        'page_number': page_number,
        'total_pages': course.total_pages,
        'image_url':   f"{media_prefix}{rel_base}/{png_name}",
        'audio_url':   f"{media_prefix}{rel_base}/audio/{mp3_name}" if mp3_path.exists() else None,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_course_ask(request, course_id):
    try:
        course = AICourse.objects.get(id=course_id)
    except AICourse.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    question = request.data.get('question', '').strip()
    if not question:
        return Response({'error': 'question is required.'}, status=status.HTTP_400_BAD_REQUEST)

    from .ai_pipeline import query_rag
    try:
        answer = query_rag(Path(course.output_dir), course.id, question)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'answer': answer})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_course_reformulate(request, course_id):
    try:
        course = AICourse.objects.get(id=course_id)
    except AICourse.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    question        = request.data.get('question', '').strip()
    previous_answer = request.data.get('previous_answer', '').strip()

    if not question:
        return Response({'error': 'question is required.'}, status=status.HTTP_400_BAD_REQUEST)

    from .ai_pipeline import query_rag
    try:
        answer = query_rag(
            Path(course.output_dir), course.id, question,
            reformulate=True, previous_answer=previous_answer,
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'answer': answer})


# ── Concept Animation Endpoints ───────────────────────────────────────────────

def _anim_data(anim, request):
    video_url = None
    if anim.video_file:
        video_url = request.build_absolute_uri(settings.MEDIA_URL + str(anim.video_file))
    return {
        'id':          anim.id,
        'concept':     anim.concept,
        'status':      anim.status,
        'video_url':   video_url,
        'error':       anim.error_msg if anim.status == 'ERROR' else None,
        'retry_count': anim.retry_count,
        'created_at':  anim.created_at.isoformat(),
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_concept_animation(request, course_id):
    concept = request.data.get('concept', '').strip()
    if not concept:
        return Response({'error': 'Concept is required.'}, status=status.HTTP_400_BAD_REQUEST)

    concept_key = concept.lower()

    existing = ConceptAnimation.objects.filter(
        ai_course_id=course_id, concept_key=concept_key
    ).order_by('-created_at').first()

    if existing and existing.status == 'READY':
        return Response({'animation_id': existing.id, 'status': 'READY', 'cached': True})
    if existing and existing.status in ('PENDING', 'GENERATING', 'RENDERING'):
        return Response({'animation_id': existing.id, 'status': existing.status, 'cached': True})

    try:
        anim = ConceptAnimation.objects.create(
            ai_course_id=course_id,
            concept=concept,
            concept_key=concept_key,
        )
    except Exception:
        existing = ConceptAnimation.objects.get(ai_course_id=course_id, concept_key=concept_key)
        return Response({'animation_id': existing.id, 'status': existing.status, 'cached': True})

    from .manim_pipeline import run_animation_in_background
    run_animation_in_background(anim.id)

    return Response({'animation_id': anim.id, 'status': 'PENDING', 'cached': False}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_animation_status(request, animation_id):
    anim = get_object_or_404(ConceptAnimation, id=animation_id)
    return Response(_anim_data(anim, request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_course_animations(request, course_id):
    animations = ConceptAnimation.objects.filter(ai_course_id=course_id).order_by('-created_at')
    return Response([_anim_data(a, request) for a in animations])


# ── Quiz Endpoints ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_quiz_view(request, class_id, course_id):
    if not Class.objects.filter(id=class_id, teacher=request.user).exists():
        return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    ai_course = get_object_or_404(AICourse, id=course_id, class_obj_id=class_id)

    if ai_course.status != 'READY':
        return Response({'error': 'Course is not ready yet.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quiz = ai_course.quiz
        if quiz.status == 'READY':
            return Response({'quiz_id': quiz.id, 'status': 'READY', 'message': 'Quiz already exists.'})
        if quiz.status in ('GENERATING', 'PENDING'):
            return Response({'quiz_id': quiz.id, 'status': quiz.status})
        if quiz.status == 'ERROR':
            quiz.delete()
    except Quiz.DoesNotExist:
        pass

    quiz = Quiz.objects.create(ai_course=ai_course, status='PENDING')
    from .quiz_pipeline import run_quiz_generation_in_background
    run_quiz_generation_in_background(quiz.id)
    return Response({'quiz_id': quiz.id, 'status': 'PENDING'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_status(request, course_id):
    ai_course = get_object_or_404(AICourse, id=course_id)
    try:
        quiz = ai_course.quiz
    except Quiz.DoesNotExist:
        return Response({'status': 'NOT_GENERATED'})
    return Response({
        'quiz_id':        quiz.id,
        'status':         quiz.status,
        'question_count': len(quiz.questions),
        'error':          quiz.error_msg if quiz.status == 'ERROR' else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_questions(request, course_id):
    ai_course = get_object_or_404(AICourse, id=course_id)
    try:
        quiz = ai_course.quiz
    except Quiz.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if quiz.status != 'READY':
        return Response({'error': 'Quiz is not ready.'}, status=status.HTTP_404_NOT_FOUND)
    safe_questions = [
        {'question': q['question'], 'options': q['options']}
        for q in quiz.questions
    ]
    return Response({'quiz_id': quiz.id, 'questions': safe_questions})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz_attempt(request, course_id):
    ai_course = get_object_or_404(AICourse, id=course_id)
    try:
        quiz = ai_course.quiz
    except Quiz.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if quiz.status != 'READY':
        return Response({'error': 'Quiz is not ready.'}, status=status.HTTP_404_NOT_FOUND)

    answers = request.data.get('answers', [])
    if (
        not isinstance(answers, list)
        or len(answers) != QUIZ_QUESTION_COUNT
        or not all(isinstance(a, int) and a in range(QUIZ_OPTION_COUNT) for a in answers)
    ):
        return Response(
            {'error': f'answers must be a list of {QUIZ_QUESTION_COUNT} integers (0–{QUIZ_OPTION_COUNT - 1}).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    correct_count = sum(
        1 for i, ans in enumerate(answers)
        if i < len(quiz.questions) and ans == quiz.questions[i]['correct_index']
    )
    score = round(correct_count / QUIZ_QUESTION_COUNT * 100)

    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user,
        answers=answers,
        score=score,
        correct_count=correct_count,
    )

    results = [
        {
            'question':       quiz.questions[i]['question'],
            'options':        quiz.questions[i]['options'],
            'selected_index': answers[i],
            'correct_index':  quiz.questions[i]['correct_index'],
            'is_correct':     answers[i] == quiz.questions[i]['correct_index'],
        }
        for i in range(QUIZ_QUESTION_COUNT)
    ]

    return Response({
        'attempt_id':    attempt.id,
        'score':         score,
        'correct_count': correct_count,
        'total':         QUIZ_QUESTION_COUNT,
        'results':       results,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_results_for_teacher(request, class_id, course_id):
    if not Class.objects.filter(id=class_id, teacher=request.user).exists():
        return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    ai_course = get_object_or_404(AICourse, id=course_id, class_obj_id=class_id)

    try:
        quiz = ai_course.quiz
    except Quiz.DoesNotExist:
        return Response({'status': 'NOT_GENERATED', 'attempts': []})

    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student').order_by('-completed_at')

    return Response({
        'quiz_id':        quiz.id,
        'status':         quiz.status,
        'question_count': len(quiz.questions),
        'attempts': [
            {
                'attempt_id':    a.id,
                'student_name':  a.student.get_full_name() or a.student.email,
                'student_email': a.student.email,
                'score':         a.score,
                'correct_count': a.correct_count,
                'total':         QUIZ_QUESTION_COUNT,
                'completed_at':  a.completed_at.isoformat(),
            }
            for a in attempts
        ],
    })
