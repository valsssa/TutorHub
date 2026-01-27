"""DTO helpers for tutor profile aggregate."""

from decimal import Decimal

from schemas import (
    TutorAvailabilityResponse,
    TutorCertificationResponse,
    TutorEducationResponse,
    TutorPricingOptionResponse,
    TutorProfileResponse,
    TutorPublicProfile,
    TutorSubjectResponse,
)

from ..domain.entities import (
    TutorAvailabilityEntity,
    TutorCertificationEntity,
    TutorEducationEntity,
    TutorPricingOptionEntity,
    TutorProfileAggregate,
    TutorSubjectEntity,
)


def _availability_to_response(
    entity: TutorAvailabilityEntity,
) -> TutorAvailabilityResponse:
    data = {
        "id": entity.id or 0,
        "day_of_week": entity.day_of_week,
        "start_time": entity.start_time,
        "end_time": entity.end_time,
        "is_recurring": entity.is_recurring,
    }
    return TutorAvailabilityResponse.model_validate(data)


def _subject_to_response(entity: TutorSubjectEntity) -> TutorSubjectResponse:
    data = {
        "id": entity.id or 0,
        "subject_id": entity.subject_id,
        "subject_name": entity.subject_name or "",
        "proficiency_level": entity.proficiency_level,
        "years_experience": entity.years_experience,
    }
    return TutorSubjectResponse.model_validate(data)


def _certification_to_response(
    entity: TutorCertificationEntity,
) -> TutorCertificationResponse:
    data = {
        "id": entity.id or 0,
        "name": entity.name,
        "issuing_organization": entity.issuing_organization,
        "issue_date": entity.issue_date,
        "expiration_date": entity.expiration_date,
        "credential_id": entity.credential_id,
        "credential_url": entity.credential_url,
        "document_url": entity.document_url,
    }
    return TutorCertificationResponse.model_validate(data)


def _education_to_response(entity: TutorEducationEntity) -> TutorEducationResponse:
    data = {
        "id": entity.id or 0,
        "institution": entity.institution,
        "degree": entity.degree,
        "field_of_study": entity.field_of_study,
        "start_year": entity.start_year,
        "end_year": entity.end_year,
        "description": entity.description,
        "document_url": entity.document_url,
    }
    return TutorEducationResponse.model_validate(data)


def _pricing_option_to_response(
    entity: TutorPricingOptionEntity,
) -> TutorPricingOptionResponse:
    data = {
        "id": entity.id or 0,
        "title": entity.title,
        "description": entity.description,
        "duration_minutes": entity.duration_minutes,
        "price": Decimal(entity.price),
    }
    return TutorPricingOptionResponse.model_validate(data)


def aggregate_to_profile_response(
    aggregate: TutorProfileAggregate,
) -> TutorProfileResponse:
    """Convert aggregate to TutorProfileResponse DTO."""
    data = {
        "id": aggregate.id,
        "user_id": aggregate.user_id,
        "name": f"{aggregate.first_name or ''} {aggregate.last_name or ''}".strip() or "Unknown",
        "title": aggregate.title or "",
        "headline": aggregate.headline,
        "bio": aggregate.bio,
        "description": aggregate.description,
        "hourly_rate": Decimal(aggregate.hourly_rate),
        "experience_years": aggregate.experience_years,
        "education": aggregate.education,
        "languages": aggregate.languages,
        "video_url": aggregate.video_url,
        "is_approved": aggregate.is_approved,
        "profile_status": aggregate.profile_status,
        "rejection_reason": aggregate.rejection_reason,
        "average_rating": Decimal(aggregate.average_rating),
        "total_reviews": aggregate.total_reviews,
        "total_sessions": aggregate.total_sessions,
        "created_at": aggregate.created_at,
        "timezone": aggregate.timezone,
        "version": aggregate.version,
        "profile_photo_url": aggregate.profile_photo_url,
        "subjects": [_subject_to_response(s) for s in aggregate.subjects],
        "availabilities": [_availability_to_response(a) for a in aggregate.availabilities],
        "certifications": [_certification_to_response(c) for c in aggregate.certifications],
        "educations": [_education_to_response(e) for e in aggregate.educations],
        "pricing_options": [_pricing_option_to_response(p) for p in aggregate.pricing_options],
    }
    return TutorProfileResponse.model_validate(data)


def aggregate_to_public_profile(aggregate: TutorProfileAggregate) -> TutorPublicProfile:
    """Convert aggregate to TutorPublicProfile DTO."""
    subjects: list[str] = [subject.subject_name or "" for subject in aggregate.subjects]
    
    # Format education list from educations entities
    education_list: list[str] = []
    for edu in aggregate.educations[:3]:  # Limit to top 3
        edu_str = f"{edu.degree or ''} in {edu.field_of_study or ''} - {edu.institution}".strip()
        if edu_str and edu_str != " in  - ":
            education_list.append(edu_str)
    
    # If no structured education, use the legacy education field
    if not education_list and aggregate.education:
        education_list = [aggregate.education]
    
    data = {
        "id": aggregate.id,
        "user_id": aggregate.user_id,
        "first_name": aggregate.first_name,
        "last_name": aggregate.last_name,
        "title": aggregate.title or "",
        "headline": aggregate.headline,
        "bio": aggregate.bio,
        "hourly_rate": aggregate.hourly_rate,
        "experience_years": aggregate.experience_years,
        "average_rating": aggregate.average_rating,
        "total_reviews": aggregate.total_reviews,
        "total_sessions": aggregate.total_sessions,
        "subjects": subjects,
        "education": education_list,
        "profile_photo_url": aggregate.profile_photo_url,
        "recent_review": None,  # Will be populated by service layer if needed
        "next_available_slots": [],  # Will be populated by service layer if needed
    }
    return TutorPublicProfile.model_validate(data)
