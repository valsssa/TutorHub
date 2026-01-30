"""Sample data seeding script for development and testing."""

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_password_hash
from database import SessionLocal
from models import (
    Booking,
    Message,
    Review,
    StudentProfile,
    Subject,
    TutorProfile,
    User,
)


def seed_subjects(db: Session):
    """Create sample subjects."""
    subjects = [
        ("Mathematics", "Algebra, Calculus, Geometry, Statistics"),
        ("Physics", "Mechanics, Thermodynamics, Electromagnetism"),
        ("Chemistry", "Organic Chemistry, Inorganic Chemistry, Biochemistry"),
        ("Biology", "Cell Biology, Genetics, Ecology"),
        ("English", "Literature, Grammar, Writing, Reading Comprehension"),
        ("Spanish", "Conversation, Grammar, Business Spanish"),
        ("Computer Science", "Programming, Algorithms, Data Structures"),
        ("History", "World History, American History, European History"),
    ]

    for name, description in subjects:
        existing = db.query(Subject).filter(Subject.name == name).first()
        if not existing:
            subject = Subject(name=name, description=description, is_active=True)
            db.add(subject)

    db.commit()


def seed_users_and_profiles(db: Session):
    """Create sample users with profiles."""
    # Create students
    students_data = [
        ("sarah.johnson@example.com", "Sarah", "Johnson"),
        ("michael.chen@example.com", "Michael", "Chen"),
        ("emily.rodriguez@example.com", "Emily", "Rodriguez"),
        ("david.kim@example.com", "David", "Kim"),
        ("alex.thompson@example.com", "Alex", "Thompson"),
        ("jamie.wilson@example.com", "Jamie", "Wilson"),
        ("taylor.smith@example.com", "Taylor", "Smith"),
        ("jordan.lee@example.com", "Jordan", "Lee"),
    ]

    for email, first_name, last_name in students_data:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=get_password_hash("student123"),
                role="student",
                is_verified=True,
                first_name=first_name,
                last_name=last_name,
            )
            db.add(user)
            db.commit()

            profile = StudentProfile(
                user_id=user.id,
                phone=f"+1{random.randint(2000000000, 9999999999)}",
                bio="Student interested in learning various subjects.",
                grade_level=random.choice(["9th Grade", "10th Grade", "11th Grade", "12th Grade"]),
                total_sessions=random.randint(0, 20),
            )
            db.add(profile)

    db.commit()

    # Create tutors
    tutors_data = [
        (
            "maria.garcia@example.com",
            "Maria",
            "Garcia",
            "Mathematics",
            "PhD in Mathematics",
        ),
        ("robert.chen@example.com", "Robert", "Chen", "Physics", "MSc in Physics"),
        ("lisa.park@example.com", "Lisa", "Park", "Chemistry", "PhD in Chemistry"),
        ("james.wilson@example.com", "James", "Wilson", "Biology", "MSc in Biology"),
        (
            "anna.mueller@example.com",
            "Anna",
            "Mueller",
            "English",
            "MA in English Literature",
        ),
        (
            "carlos.martinez@example.com",
            "Carlos",
            "Martinez",
            "Spanish",
            "Native Speaker",
        ),
    ]

    for email, first_name, last_name, subject_name, education in tutors_data:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=get_password_hash("tutor123"),
                role="tutor",
                is_verified=True,
                first_name=first_name,
                last_name=last_name,
            )
            db.add(user)
            db.commit()

            # Tutor profile is created automatically by trigger
            # Now update it
            tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == user.id).first()
            if tutor_profile:
                tutor_profile.title = f"Expert {subject_name} Tutor"
                tutor_profile.headline = f"{random.randint(5, 15)}+ years teaching experience"
                tutor_profile.bio = f"Passionate about helping students excel in {subject_name}."
                tutor_profile.description = (
                    f"I have been teaching {subject_name} for over {random.randint(5, 15)} years "
                    f"and have helped hundreds of students achieve their academic goals. "
                    f"My teaching approach is student-centered and focuses on building "
                    f"strong foundational knowledge."
                )
                tutor_profile.hourly_rate = Decimal(random.choice([35, 40, 45, 50, 55, 60]))
                tutor_profile.experience_years = random.randint(5, 15)
                tutor_profile.education = education
                tutor_profile.languages = random.choice([["English"], ["English", "Spanish"], ["English", "Chinese"]])
                tutor_profile.is_approved = True
                tutor_profile.profile_status = "approved"
                tutor_profile.approved_at = datetime.now(UTC) - timedelta(days=random.randint(30, 365))
                tutor_profile.average_rating = Decimal(random.uniform(4.5, 5.0))
                tutor_profile.total_reviews = random.randint(10, 50)
                tutor_profile.total_sessions = random.randint(50, 200)

    db.commit()


def seed_bookings(db: Session):
    """Create sample bookings."""
    students = db.query(User).filter(User.role == "student").all()
    tutors = db.query(TutorProfile).filter(TutorProfile.is_approved.is_(True)).all()
    subjects = db.query(Subject).all()

    if not students or not tutors or not subjects:
        return

    now = datetime.now(UTC)

    # Create past bookings (completed)
    for _i in range(20):
        student = random.choice(students)
        tutor = random.choice(tutors)
        subject = random.choice(subjects)

        start_time = now - timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
        end_time = start_time + timedelta(minutes=random.choice([30, 45, 60, 90]))

        # Get profile data for names
        tutor_user_profile = db.query(User).filter(User.id == tutor.user_id).first()
        db.query(StudentProfile).filter(StudentProfile.user_id == student.id).first()

        # Build names using user data (single source of truth)
        tutor_name = (
            f"{tutor_user_profile.first_name or ''} {tutor_user_profile.last_name or ''}".strip()
            if tutor_user_profile and (tutor_user_profile.first_name or tutor_user_profile.last_name)
            else tutor.user.email
        )
        student_name = (
            f"{student.first_name or ''} {student.last_name or ''}".strip()
            if student and (student.first_name or student.last_name)
            else student.email
        )

        # Simple insert without JSONB fields - let database defaults handle them
        db.execute(
            text(
                """
            INSERT INTO bookings (
                tutor_profile_id, student_id, subject_id,
                start_time, end_time, status, topic,
                hourly_rate, total_amount,
                tutor_name, student_name, subject_name
            ) VALUES (
                :tutor_id, :student_id, :subject_id,
                :start_time, :end_time, :status, :topic,
                :hourly_rate, :total_amount,
                :tutor_name, :student_name, :subject_name
            )
            """
            ),
            {
                "tutor_id": tutor.id,
                "student_id": student.id,
                "subject_id": subject.id,
                "start_time": start_time,
                "end_time": end_time,
                "status": "completed",
                "topic": f"Study session on {subject.name}",
                "hourly_rate": float(tutor.hourly_rate),
                "total_amount": float(tutor.hourly_rate * Decimal((end_time - start_time).total_seconds() / 3600)),
                "tutor_name": tutor_name,
                "student_name": student_name,
                "subject_name": subject.name,
            },
        )

    # Create upcoming bookings (confirmed/pending)
    for _i in range(10):
        student = random.choice(students)
        tutor = random.choice(tutors)
        subject = random.choice(subjects)

        start_time = now + timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
        end_time = start_time + timedelta(minutes=random.choice([30, 45, 60, 90]))

        # Get profile data for names
        tutor_user_profile = db.query(User).filter(User.id == tutor.user_id).first()
        db.query(StudentProfile).filter(StudentProfile.user_id == student.id).first()

        # Build names using user data (single source of truth)
        tutor_name = (
            f"{tutor_user_profile.first_name or ''} {tutor_user_profile.last_name or ''}".strip()
            if tutor_user_profile and (tutor_user_profile.first_name or tutor_user_profile.last_name)
            else tutor.user.email
        )
        student_name = (
            f"{student.first_name or ''} {student.last_name or ''}".strip()
            if student and (student.first_name or student.last_name)
            else student.email
        )

        db.execute(
            text(
                """
            INSERT INTO bookings (
                tutor_profile_id, student_id, subject_id,
                start_time, end_time, status, topic,
                hourly_rate, total_amount,
                tutor_name, student_name, subject_name
            ) VALUES (
                :tutor_id, :student_id, :subject_id,
                :start_time, :end_time, :status, :topic,
                :hourly_rate, :total_amount,
                :tutor_name, :student_name, :subject_name
            )
            """
            ),
            {
                "tutor_id": tutor.id,
                "student_id": student.id,
                "subject_id": subject.id,
                "start_time": start_time,
                "end_time": end_time,
                "status": random.choice(["confirmed", "pending"]),
                "topic": f"Study session on {subject.name}",
                "hourly_rate": float(tutor.hourly_rate),
                "total_amount": float(tutor.hourly_rate * Decimal((end_time - start_time).total_seconds() / 3600)),
                "tutor_name": tutor_name,
                "student_name": student_name,
                "subject_name": subject.name,
            },
        )

    db.commit()


def seed_reviews(db: Session):
    """Create sample reviews."""
    completed_bookings = db.query(Booking).filter(
        Booking.session_state == "ENDED",
        Booking.session_outcome == "COMPLETED"
    ).all()

    for booking in completed_bookings[:15]:  # Add reviews to half of completed bookings
        existing = db.query(Review).filter(Review.booking_id == booking.id).first()
        if not existing:
            rating = random.randint(4, 5)
            comments = [
                "Great tutor! Very helpful and patient.",
                "Excellent session. Learned a lot!",
                "Highly recommend this tutor.",
                "Very knowledgeable and explains concepts well.",
                "Amazing tutor. Will book again!",
            ]

            # Use raw SQL to avoid JSONB field issue
            db.execute(
                text(
                    """
                INSERT INTO reviews (
                    booking_id, tutor_profile_id, student_id,
                    rating, comment, is_public
                ) VALUES (
                    :booking_id, :tutor_profile_id, :student_id,
                    :rating, :comment, :is_public
                )
                """
                ),
                {
                    "booking_id": booking.id,
                    "tutor_profile_id": booking.tutor_profile_id,
                    "student_id": booking.student_id,
                    "rating": rating,
                    "comment": random.choice(comments),
                    "is_public": True,
                },
            )

    db.commit()


def seed_messages(db: Session):
    """Create sample messages."""
    students = db.query(User).filter(User.role == "student").all()
    tutors_users = db.query(User).filter(User.role == "tutor").all()
    admin = db.query(User).filter(User.role == "admin").first()

    if not students or not tutors_users or not admin:
        return

    # Create some messages between students and tutors
    for _ in range(10):
        student = random.choice(students)
        tutor = random.choice(tutors_users)

        message1 = Message(
            sender_id=student.id,
            recipient_id=tutor.id,
            message=random.choice(
                [
                    "Hi! I'd like to schedule a session with you.",
                    "Thank you for the great session today!",
                    "Can we reschedule our next session?",
                    "I have a question about the homework.",
                ]
            ),
            is_read=random.choice([True, False]),
        )
        db.add(message1)

        # Some replies
        if random.random() > 0.5:
            message2 = Message(
                sender_id=tutor.id,
                recipient_id=student.id,
                message=random.choice(
                    [
                        "Sure! I'm available tomorrow afternoon.",
                        "You're welcome! Happy to help.",
                        "Of course! When works best for you?",
                        "Feel free to ask anything.",
                    ]
                ),
                is_read=random.choice([True, False]),
            )
            db.add(message2)

    db.commit()


def main():
    """Run all seeding functions."""

    db = SessionLocal()
    try:
        seed_subjects(db)
        seed_users_and_profiles(db)
        seed_bookings(db)
        seed_reviews(db)
        seed_messages(db)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
