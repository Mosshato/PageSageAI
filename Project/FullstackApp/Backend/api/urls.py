from django.urls import path
from . import views, auth_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────────────────
    path('auth/signup/',        auth_views.signup),
    path('auth/login/',         auth_views.login),
    path('auth/me/',            auth_views.me),
    path('auth/token/refresh/', TokenRefreshView.as_view()),

    # ── Classes ──────────────────────────────────────────────────────────────
    path('classes/',                    views.class_list),
    path('classes/enroll/',             views.enroll),
    path('classes/<int:class_id>/',         views.class_detail),
    path('classes/<int:class_id>/quit/',    views.quit_class),

    # ── Assignments ───────────────────────────────────────────────────────────
    path('assignments/',                                    views.all_assignments),
    path('assignments/<int:assignment_id>/submit/',         views.submit_assignment),   # POST = submit/resubmit
    path('assignments/<int:assignment_id>/unsubmit/',       views.unsubmit_assignment), # DELETE = unsubmit

    # ── Account ───────────────────────────────────────────────────────────────
    path('account/stats/',  views.account_stats),

    # ── Teacher ───────────────────────────────────────────────────────────────
    path('teacher/classes/',                                                    views.teacher_class_list),
    path('teacher/stats/',                                                      views.teacher_stats),
    path('teacher/students/',                                                   views.teacher_students),
    path('teacher/classes/<int:class_id>/',                                     views.teacher_class_detail),
    path('teacher/classes/<int:class_id>/students/',                            views.teacher_add_student),
    path('teacher/classes/<int:class_id>/students/<int:enrollment_id>/',        views.teacher_remove_student),
    path('teacher/classes/<int:class_id>/announcements/',                       views.teacher_add_announcement),
    path('teacher/classes/<int:class_id>/announcements/<int:announcement_id>/', views.teacher_delete_announcement),
    path('teacher/classes/<int:class_id>/assignments/',                         views.teacher_add_assignment),
    path('teacher/classes/<int:class_id>/assignments/<int:assignment_id>/',     views.teacher_delete_assignment),
    path('teacher/classes/<int:class_id>/assignments/<int:assignment_id>/edit/', views.teacher_edit_assignment),
    path('teacher/classes/<int:class_id>/lectures/',                            views.teacher_add_lecture),
    path('teacher/classes/<int:class_id>/lectures/<int:lecture_id>/',           views.teacher_delete_lecture),
    path('teacher/classes/<int:class_id>/submissions/<int:submission_id>/grade/', views.teacher_grade_submission),

    # ── AI Teaching ───────────────────────────────────────────────────────────
    path('teacher/classes/<int:class_id>/ai-courses/',          views.teacher_upload_ai_course),
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/', views.teacher_delete_ai_course),
    path('ai-courses/class/<int:class_id>/',                    views.ai_courses_for_class),
    path('ai-courses/<int:course_id>/status/',                  views.ai_course_status),
    path('ai-courses/<int:course_id>/page/<int:page_number>/',  views.ai_course_page),
    path('ai-courses/<int:course_id>/ask/',                     views.ai_course_ask),
    path('ai-courses/<int:course_id>/reformulate/',             views.ai_course_reformulate),

    # ── Concept Animations ────────────────────────────────────────────────────
    path('ai-courses/<int:course_id>/animations/',       views.request_concept_animation),
    path('ai-courses/<int:course_id>/animations/list/',  views.list_course_animations),
    path('animations/<int:animation_id>/status/',        views.get_animation_status),

    # ── Quiz ──────────────────────────────────────────────────────────────────
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/generate-quiz/', views.generate_quiz_view),
    path('teacher/classes/<int:class_id>/ai-courses/<int:course_id>/quiz-results/',  views.get_quiz_results_for_teacher),
    path('ai-courses/<int:course_id>/quiz/status/',    views.get_quiz_status),
    path('ai-courses/<int:course_id>/quiz/questions/', views.get_quiz_questions),
    path('ai-courses/<int:course_id>/quiz/attempt/',   views.submit_quiz_attempt),
]
