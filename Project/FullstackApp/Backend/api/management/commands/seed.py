from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.domain import Class, Announcement, Assignment, AssignmentAttachment, Lecture, LectureFile, Enrollment
from datetime import date, timedelta

User = get_user_model()

TODAY = date.today()


class Command(BaseCommand):
    help = 'Seed database with demo data'

    def handle(self, *args, **options):
        # ── Demo users ───────────────────────────────────────────────────────
        if not User.objects.filter(email='teacher@pagesageai.com').exists():
            User.objects.create_user(
                email='teacher@pagesageai.com', password='test1234',
                role='teacher', first_name='Alex', last_name='Carter',
            )
            self.stdout.write('Created teacher: teacher@pagesageai.com / test1234')

        if not User.objects.filter(email='student@demo.com').exists():
            User.objects.create_user(
                email='student@demo.com', password='test1234',
                role='student', first_name='Demo', last_name='Student',
            )
            self.stdout.write('Created student: student@demo.com / test1234')

        teacher = User.objects.get(email='teacher@pagesageai.com')
        Class.objects.all().delete()

        math = Class.objects.create(name='Mathematics', teacher_name='Dr. Smith', code='MATH01', color='#f97316', icon='📐')
        cs = Class.objects.create(name='Computer Science', teacher_name='Prof. Johnson', code='CS101', color='#10b981', icon='💻')
        phys = Class.objects.create(name='Physics', teacher_name='Dr. Lee', code='PHYS01', color='#3b82f6', icon='⚛️')
        lit = Class.objects.create(name='Literature', teacher_name='Ms. Davis', code='LIT101', color='#8b5cf6', icon='📖')

        for cls, announcements in [
            (math, [
                ('Midterm Results Posted', 'The midterm results have been posted on the portal. Office hours this week are extended.', True),
                ('Problem Set 4 Released', 'Problem Set 4 is now available. It covers chapters 7-9 and is due next Friday.', False),
            ]),
            (cs, [
                ('Lab 2 Guidelines Updated', 'Please review the updated guidelines before starting Lab Assignment 2.', True),
                ('Guest Lecture Next Week', 'We will have a guest lecturer from Google next Thursday.', False),
            ]),
            (phys, [
                ('Quiz Rescheduled', 'The Chapter 5 quiz has been moved to Monday due to the lab session.', True),
            ]),
            (lit, [
                ('Essay Feedback', 'Individual feedback for Essay Draft has been emailed to all students.', False),
            ]),
        ]:
            for title, body, pinned in announcements:
                Announcement.objects.create(class_obj=cls, title=title, body=body, pinned=pinned)

        assignments_data = [
            (math, 'Problem Set 4', 'Solve problems from chapters 7-9 covering integration techniques.', TODAY + timedelta(days=1), 100, 'pending', None, ['ps4_instructions.pdf']),
            (cs, 'Lab Assignment 2', 'Implement a binary search tree with insert, delete, and search operations.', TODAY + timedelta(days=2), 100, 'pending', None, ['lab2_starter.zip', 'lab2_spec.pdf']),
            (cs, 'Project Proposal', 'Write a 2-page proposal for your semester project.', TODAY + timedelta(days=4), 50, 'pending', None, []),
            (phys, 'Chapter 5 Quiz', 'Online quiz covering kinematics and dynamics.', TODAY + timedelta(days=5), 50, 'pending', None, []),
            (math, 'Problem Set 3', 'Differentiation and integration basics.', TODAY - timedelta(days=7), 100, 'submitted', None, ['ps3_instructions.pdf']),
            (cs, 'Lab Assignment 1', 'Basic data structures implementation.', TODAY - timedelta(days=10), 100, 'submitted', None, []),
            (phys, 'Chapter 4 Quiz', 'Energy and momentum quiz.', TODAY - timedelta(days=5), 50, 'graded', 76, []),
            (lit, 'Essay Draft', 'Draft essay on themes in modern literature.', TODAY - timedelta(days=3), 100, 'graded', 95, ['essay_rubric.pdf']),
            (math, 'Midterm Exam', 'Comprehensive midterm covering all topics.', TODAY - timedelta(days=14), 200, 'graded', 84, []),
            (math, 'Calculus Review', 'Derivatives review.', TODAY + timedelta(days=2), 50, 'pending', None, []),
            (phys, 'Optics Lab', 'Light refraction experiment report.', TODAY + timedelta(days=2), 75, 'pending', None, ['optics_guide.pdf']),
            (lit, 'Poetry Analysis', 'Analyze three poems from the anthology.', TODAY + timedelta(days=2), 100, 'pending', None, []),
        ]

        for cls, title, desc, due, pts, stat, grade, files in assignments_data:
            a = Assignment.objects.create(class_obj=cls, title=title, description=desc, due_date=due, points=pts, status=stat, grade=grade)
            for f in files:
                AssignmentAttachment.objects.create(assignment=a, name=f)

        lectures_data = [
            (math, [
                ('Introduction to Calculus', 'Overview of limits, derivatives and the fundamental theorem.', '52 min', TODAY - timedelta(days=30), ['calculus_intro.pdf', 'notes_week1.pdf']),
                ('Differentiation Rules', 'Chain rule, product rule and quotient rule with examples.', '48 min', TODAY - timedelta(days=23), ['diff_rules.pdf']),
                ('Integration Techniques', 'Substitution, integration by parts, and partial fractions.', '55 min', TODAY - timedelta(days=16), ['integration.pdf', 'practice_problems.pdf']),
            ]),
            (cs, [
                ('Data Structures Overview', 'Arrays, linked lists, stacks, queues and their complexity.', '60 min', TODAY - timedelta(days=28), ['ds_slides.pdf']),
                ('Trees and Graphs', 'Binary trees, BSTs, graph representations and traversals.', '65 min', TODAY - timedelta(days=21), ['trees_graphs.pdf', 'code_examples.zip']),
                ('Sorting Algorithms', 'QuickSort, MergeSort, HeapSort analysis and implementations.', '58 min', TODAY - timedelta(days=14), ['sorting.pdf']),
                ('Dynamic Programming', 'Memoization, tabulation, and classic DP problems.', '70 min', TODAY - timedelta(days=7), ['dp_slides.pdf', 'dp_problems.pdf']),
            ]),
            (phys, [
                ('Kinematics', 'Motion in 1D and 2D, projectile motion.', '50 min', TODAY - timedelta(days=25), ['kinematics.pdf']),
                ('Newton Laws', 'Forces, free-body diagrams, and Newton three laws.', '55 min', TODAY - timedelta(days=18), ['newton.pdf', 'lab_guide.pdf']),
                ('Energy and Momentum', 'Conservation laws and collisions.', '48 min', TODAY - timedelta(days=11), ['energy.pdf']),
            ]),
            (lit, [
                ('Modernism in Literature', 'Key characteristics and major authors of modernism.', '45 min', TODAY - timedelta(days=20), ['modernism.pdf']),
                ('Poetry Analysis Methods', 'Meter, rhyme, imagery, and close reading techniques.', '40 min', TODAY - timedelta(days=13), ['poetry_guide.pdf']),
            ]),
        ]

        for cls, lecs in lectures_data:
            for title, desc, dur, dt, files in lecs:
                lec = Lecture.objects.create(class_obj=cls, title=title, description=desc, duration=dur, date=dt)
                for f in files:
                    LectureFile.objects.create(lecture=lec, name=f)

        Enrollment.objects.create(class_obj=math, student_email='student@demo.com', student_name='Demo Student')
        Enrollment.objects.create(class_obj=cs, student_email='student@demo.com', student_name='Demo Student')
        Enrollment.objects.create(class_obj=phys, student_email='student@demo.com', student_name='Demo Student')
        Enrollment.objects.create(class_obj=lit, student_email='student@demo.com', student_name='Demo Student')

        for cls in [math, cs, phys, lit]:
            for name, email in [('Alice Chen', 'alice@school.edu'), ('Bob Martin', 'bob@school.edu'), ('Carol White', 'carol@school.edu')]:
                Enrollment.objects.get_or_create(class_obj=cls, student_email=email, defaults={'student_name': name})

        # ── Demo class created by the teacher (enrollable via code DEMO01) ──
        demo = Class.objects.create(
            name='Introduction to AI', teacher_name='Dr. Alex Carter',
            teacher=teacher, code='DEMO01', color='#ec4899', icon='🤖',
        )
        Announcement.objects.create(class_obj=demo, title='Welcome to Intro to AI!',
            body='Welcome everyone! This course covers the fundamentals of artificial intelligence, machine learning, and neural networks. Office hours are every Tuesday 3-5pm.', pinned=True)
        Announcement.objects.create(class_obj=demo, title='First Assignment Released',
            body='The first assignment on linear regression has been posted. It is due in one week. Make sure to read chapters 1-3 before starting.', pinned=False)

        a1 = Assignment.objects.create(class_obj=demo, title='Linear Regression Lab',
            description='Implement linear regression from scratch using NumPy. Compare your results with scikit-learn.',
            due_date=TODAY + timedelta(days=6), points=100, status='pending')
        AssignmentAttachment.objects.create(assignment=a1, name='lab1_starter.ipynb')
        AssignmentAttachment.objects.create(assignment=a1, name='dataset.csv')

        a2 = Assignment.objects.create(class_obj=demo, title='Neural Network Essay',
            description='Write a 1000-word essay on the history and impact of neural networks.',
            due_date=TODAY + timedelta(days=12), points=50, status='pending')

        a3 = Assignment.objects.create(class_obj=demo, title='Quiz 1 — ML Basics',
            description='Multiple choice quiz covering supervised vs unsupervised learning.',
            due_date=TODAY - timedelta(days=3), points=50, status='graded', grade=88)

        lec1 = Lecture.objects.create(class_obj=demo, title='What is Artificial Intelligence?',
            description='Overview of AI history, from Turing to modern deep learning. We cover key milestones and define narrow vs general AI.',
            duration='45 min', date=TODAY - timedelta(days=14))
        LectureFile.objects.create(lecture=lec1, name='lecture1_slides.pdf')

        lec2 = Lecture.objects.create(class_obj=demo, title='Supervised Learning',
            description='Introduction to supervised learning: regression and classification. We walk through k-NN and decision trees with practical examples.',
            duration='50 min', date=TODAY - timedelta(days=7))
        LectureFile.objects.create(lecture=lec2, name='lecture2_slides.pdf')
        LectureFile.objects.create(lecture=lec2, name='examples.ipynb')

        for name, email in [('Alice Chen', 'alice@school.edu'), ('Bob Martin', 'bob@school.edu')]:
            Enrollment.objects.get_or_create(class_obj=demo, student_email=email, defaults={'student_name': name})

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('  Demo class code: DEMO01 (Introduction to AI)')
        self.stdout.write('  Teacher login:   teacher@pagesageai.com / test1234')
