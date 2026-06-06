from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from pathlib import Path
        from django.db import OperationalError, ProgrammingError

        try:
            from .models import AICourse
            from .ai_pipeline import run_pipeline_in_background

            stuck = AICourse.objects.filter(status='PROCESSING')
            if not stuck.exists():
                return

            count = stuck.count()
            print(f"[AI Pipeline] Resuming {count} interrupted course(s)...", flush=True)
            for course in stuck:
                if not course.output_dir:
                    continue
                output_dir = Path(course.output_dir)
                pdf_path = output_dir / course.filename
                if not pdf_path.exists():
                    print(f"[AI Pipeline] Course {course.id} — PDF missing, marking ERROR", flush=True)
                    course.status = 'ERROR'
                    course.error_msg = 'PDF file not found after server restart.'
                    course.save()
                    continue
                print(f"[AI Pipeline] Course {course.id} — resuming from step {course.current_step}", flush=True)
                run_pipeline_in_background(course.id, pdf_path, output_dir)

        except (OperationalError, ProgrammingError):
            # DB not yet migrated — skip resume on first run
            pass
