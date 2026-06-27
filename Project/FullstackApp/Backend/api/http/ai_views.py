from pathlib import Path

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404

from ..domain import Class, AICourse, ConceptAnimation, Quiz, QuizAttempt
from ..constants import QUIZ_QUESTION_COUNT, QUIZ_OPTION_COUNT

# ── AI Teaching Endpoints ─────────────────────────────────────────────────────

AI_COURSES_ROOT = Path(settings.AI_COURSES_ROOT)


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

    from ..services.ai_pipeline import run_pipeline_in_background
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

    from ..services.ai_pipeline import query_rag
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

    from ..services.ai_pipeline import query_rag
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

    from ..services.manim_pipeline import run_animation_in_background
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
    from ..services.quiz_pipeline import run_quiz_generation_in_background
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
                'student_name':  f"{a.student.first_name} {a.student.last_name}".strip() or a.student.email,
                'student_email': a.student.email,
                'score':         a.score,
                'correct_count': a.correct_count,
                'total':         QUIZ_QUESTION_COUNT,
                'completed_at':  a.completed_at.isoformat(),
            }
            for a in attempts
        ],
    })
