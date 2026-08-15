"""
Seeds a complete, realistic "Mastering Django: Beginner to Enterprise"
course into the platform — instructor, 12 sections, 150+ lessons, 12 quizzes,
12 assignments, 6 judged coding exercises, 100 students, enrollments,
progress tracking, quiz attempts, assignment submissions, reviews,
certificates, and wishlist entries.

Safe to rerun: structural content (course/sections/lessons/quizzes/
assignments) is get_or_create'd by natural keys, and student activity
(enrollments/progress/attempts/etc.) only inserts rows for (student, target)
pairs that don't already exist.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.seeding import activity, assessments, curriculum, people


class Command(BaseCommand):
    help = "Seed the 'Mastering Django: Beginner to Enterprise' demo course with realistic content and activity."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding instructor and students...")
        instructor = people.get_or_create_instructor()
        students = people.get_or_create_students()

        self.stdout.write("Seeding course, categories, tags, and curriculum...")
        course = curriculum.get_or_create_course(instructor)
        sections_by_title = curriculum.build_sections_and_lessons(course)

        lesson_count = sum(len(entry["lessons"]) for entry in sections_by_title.values())
        total_seconds = sum(
            lesson.duration_seconds
            for entry in sections_by_title.values()
            for lesson in entry["lessons"]
        )

        self.stdout.write("Seeding quizzes, assignments, and coding exercises...")
        quizzes = assessments.build_quizzes(course, sections_by_title)
        course_assignments = assessments.build_assignments(course)
        coding_exercises = assessments.build_coding_exercises(course, sections_by_title)

        self.stdout.write("Enrolling students and building progress history...")
        enrollment_by_student, completed_students, active_students = activity.build_enrollments(
            course, students
        )
        activity.build_progress(
            course, sections_by_title, enrollment_by_student, completed_students, active_students
        )
        activity.build_bookmarks_and_notes(
            sections_by_title, active_students, enrollment_by_student
        )

        self.stdout.write(
            "Seeding quiz attempts, assignment submissions, and coding submissions..."
        )
        activity.build_quiz_attempts(quizzes, completed_students, enrollment_by_student)
        activity.build_assignment_submissions(
            course_assignments, completed_students, enrollment_by_student, instructor
        )
        activity.build_coding_exercise_submissions(
            coding_exercises, completed_students, enrollment_by_student
        )

        self.stdout.write("Seeding reviews, certificates, and wishlist entries...")
        activity.build_reviews(course, completed_students, enrollment_by_student)
        activity.build_certificates(completed_students, enrollment_by_student)
        activity.build_wishlist(course, active_students)

        self.stdout.write(self.style.SUCCESS("\nDone. Course seeded successfully:"))
        self.stdout.write(
            f"  Course:            {course.title}  ({course.status}, {course.get_difficulty_display()})"
        )
        self.stdout.write(f"  Sections:          {len(sections_by_title)}")
        self.stdout.write(
            f"  Lessons:           {lesson_count}  (~{total_seconds / 3600:.1f} hours)"
        )
        self.stdout.write(f"  Quizzes:           {len(quizzes)}")
        self.stdout.write(f"  Assignments:       {len(course_assignments)}")
        self.stdout.write(f"  Coding exercises:  {len(coding_exercises)}")
        self.stdout.write(f"  Students:          {len(students)}")
        self.stdout.write(f"  Completed:         {len(completed_students)}")
        self.stdout.write(f"  Active enrollees:  {len(active_students)}")
        self.stdout.write(f"\n  Dev login for any seeded account: <email> / {people.SEED_PASSWORD}")
        self.stdout.write(f"  Instructor email:  {people.INSTRUCTOR_EMAIL}")
