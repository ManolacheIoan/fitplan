"""Profile persistence and the safety rules applied when it changes."""

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.common.health_constants import MAX_AGE_YEARS, MIN_AGE_YEARS
from app.nutrition import service as nutrition_service
from app.plans import generator as plan_generator
from app.plans import service as plans_service
from app.profile import screening
from app.profile.models import Profile, ScreeningStatus
from app.profile.schemas import ProfileIn, ProfileOut

# Profile fields the screening questions depend on (the pregnancy question is asked only for
# female sex). Changing one resets the outcome, so the user must answer the screening again.
# Birth date is not listed: no question depends on age, and the 18+ rule runs on every save.
SCREENING_FIELDS = ("sex",)


class ProfileRuleError(Exception):
    """A rule violation the user must fix (code is shown by the frontend)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def today() -> date:
    return datetime.now(UTC).date()


def get(db: Session, user_id: int) -> Profile | None:
    return db.get(Profile, user_id)


def to_out(profile: Profile) -> ProfileOut:
    age = screening.age_on(profile.birth_date, today())
    return ProfileOut.model_validate({**_columns(profile), "age": age})


def _columns(profile: Profile) -> dict[str, Any]:
    return {c.key: getattr(profile, c.key) for c in Profile.__table__.columns}


def validate(data: ProfileIn) -> None:
    """Server-side eligibility checks; the client is never trusted for these."""
    age = screening.age_on(data.birth_date, today())
    if age < MIN_AGE_YEARS:
        raise ProfileRuleError("underage")
    if age > MAX_AGE_YEARS:
        raise ProfileRuleError("age_out_of_range")
    if not screening.goal_allowed(data.goal, data.weight_kg, data.height_cm):
        raise ProfileRuleError("weight_loss_blocked_bmi")
    if plan_generator.resolve_template(data.program, data.training_days) is None:
        raise ProfileRuleError("program_days_mismatch")


def save(db: Session, user_id: int, data: ProfileIn) -> Profile:
    validate(data)
    profile = get(db, user_id)
    if profile is None:
        profile = Profile(user_id=user_id, **data.model_dump())
        db.add(profile)
    else:
        if any(getattr(profile, f) != getattr(data, f) for f in SCREENING_FIELDS):
            # The questions depend on these fields: the old outcome no longer applies.
            profile.screening_status = None
            profile.screening_at = None
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
    db.flush()
    _regenerate(db, profile)
    db.commit()
    return profile


def record_screening(db: Session, profile: Profile, status: ScreeningStatus) -> None:
    profile.screening_status = status
    profile.screening_at = datetime.now(UTC)
    _regenerate(db, profile)
    db.commit()


def _regenerate(db: Session, profile: Profile) -> None:
    """Refresh everything derived from the profile (removed if screening did not pass)."""
    nutrition_service.recompute(db, profile)
    plans_service.sync_with_profile(db, profile)


def export(db: Session, user_id: int) -> dict[str, Any] | None:
    profile = get(db, user_id)
    return to_out(profile).model_dump(mode="json") if profile else None
