from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg

from ..domain import Class, Enrollment, Assignment, Submission, SubmissionFile
from .serializers import ClassSerializer, ClassDetailSerializer, AssignmentSerializer, SubmissionSerializer


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

    if not Enrollment.objects.filter(
        class_obj=assignment.class_obj,
        student_email=request.user.email,
    ).exists():
        return Response({'error': 'You are not enrolled in this class.'}, status=status.HTTP_403_FORBIDDEN)

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
