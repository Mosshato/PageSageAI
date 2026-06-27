"""Domain layer - Database models and entities."""

from .auth import User, UserManager
from .classroom import Class, Enrollment, Announcement, generate_code
from .assignment import Assignment, AssignmentAttachment, Submission, SubmissionFile
from .lecture import Lecture, LectureFile
from .ai import AICourse, ConceptAnimation, Quiz, QuizAttempt

__all__ = [
    'User',
    'UserManager',
    'Class',
    'Enrollment',
    'Announcement',
    'generate_code',
    'Assignment',
    'AssignmentAttachment',
    'Submission',
    'SubmissionFile',
    'Lecture',
    'LectureFile',
    'AICourse',
    'ConceptAnimation',
    'Quiz',
    'QuizAttempt',
]
