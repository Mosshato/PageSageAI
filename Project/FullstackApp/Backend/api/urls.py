from django.urls import path
from .http import (
    signup, login, me,
    class_list, enroll, class_detail, quit_class, all_assignments, submit_assignment, unsubmit_assignment, account_stats,
    teacher_class_list, teacher_stats, teacher_students, teacher_class_detail, teacher_add_student, teacher_remove_student,
    teacher_add_announcement, teacher_delete_announcement, teacher_add_assignment, teacher_edit_assignment, teacher_delete_assignment,
    teacher_add_lecture, teacher_delete_lecture, teacher_grade_submission,
    teacher_upload_ai_course, teacher_delete_ai_course, ai_course_status, ai_courses_for_class, ai_course_page, ai_course_ask,
    ai_course_reformulate, request_concept_animation, get_animation_status, list_course_animations,
    generate_quiz_view, get_quiz_status, get_quiz_questions, submit_quiz_attempt, get_quiz_results_for_teacher,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────────────────
    path('auth/signup/',       signup),
    path('auth/login/',        login),
    path('auth/me/',           me),
    path('auth/token/refresh/', TokenRefreshView.as_view()),

    # ── Classes ──────────────────────────────────────────────────────────────
    path('classes/',                    class_list),
    path('classes/enroll/',             enroll),
    path('classes/<int:class_id>/',         class_detail),
    path('classes/<int:class_id>/quit/',    quit_class),

    # ── Assignments ───────────────────────────────────────────────────────────
    path('assignments/',                                    all_assignments),
    path('assignments/<int:assignment_id>/submit/',         submit_assignment),   # POST = submit/resubmit
    path('assignments/<int:assignment_id>/unsubmit/',       unsubmit_assignment), # DELETE = unsubmit

    # ── Account ───────────────────────────────────────────────────────────────
    path('account/stats/',  account_stats),

    # ── Teacher ───────────────────────────────────────────────────────────────
    path('teacher/classes/',                                                    teacher_class_list),
    path('teacher/stats/',                                                      teacher_stats),
    path('teacher/students/',                                                   teacher_students),
    path('teacher/classes/<int:class_id>/',                                     teacher_class_detail),
    path('teacher/classes/<int:class_id>/students/',                            teacher_add_student),
    path('teacher/classes/<int:class_id>/students/<int:enrollment_id>/',        teacher_remove_student),
    path('teacher/classes/<int:class_id>/announcements/',                       teacher_add_announcement),
    path('teacher/classes/<int:class_id>/announcements/<int:announcement_id>/', teacher_delete_announcement),
    path('teacher/classes/<int:class_id>/assignments/',                         teacher_add_assignment),
    path('teacher/classes/<int:class_id>/assignments/<int:assignment_id>/',     teacher_delete_assignment),
    path('teacher/classes/<int:class_id>/assignments/<int:assignment_id>/edit/', teacher_edit_assignment),
    path('teacher/classes/<int:class_id>/lectures/',                            teacher_add_lecture),
    path('teacher/classes/<int:class_id>/lectures/<int:lecture_id>/',           teacher_delete_lecture),
    path('teacher/classes/<int:class_id>/submissions/<int:submission_id>/grade/', teacher_grade_submission),

    # ── AI Teaching ───────────────────────────────────────────────────────────
    path('teacher/classes/<int:class_id>/ai-courses/',          teacher_upload_ai_course),
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/', teacher_delete_ai_course),
    path('ai-courses/class/<int:class_id>/',                    ai_courses_for_class),
    path('ai-courses/<int:course_id>/status/',                  ai_course_status),
    path('ai-courses/<int:course_id>/page/<int:page_number>/',  ai_course_page),
    path('ai-courses/<int:course_id>/ask/',                     ai_course_ask),
    path('ai-courses/<int:course_id>/reformulate/',             ai_course_reformulate),

    # ── Concept Animations ────────────────────────────────────────────────────
    path('ai-courses/<int:course_id>/animations/',       request_concept_animation),
    path('ai-courses/<int:course_id>/animations/list/',  list_course_animations),
    path('animations/<int:animation_id>/status/',        get_animation_status),

    # ── Quiz ──────────────────────────────────────────────────────────────────
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/generate-quiz/', generate_quiz_view),
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/quiz-results/',  get_quiz_results_for_teacher),
    path('ai-courses/<int:course_id>/quiz/status/',    get_quiz_status),
    path('ai-courses/<int:course_id>/quiz/questions/', get_quiz_questions),
    path('ai-courses/<int:course_id>/quiz/attempt/',   submit_quiz_attempt),
]
