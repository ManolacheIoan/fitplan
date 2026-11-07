from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128

Password = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class Credentials(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RegisterIn(Credentials):
    password: str = Password
    # Registration is impossible without explicit consent (checkbox in the UI).
    consent: Literal[True]


class ConsentIn(BaseModel):
    accepted: Literal[True]


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Password


class AccountDeleteIn(BaseModel):
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class MeOut(BaseModel):
    email: str
    created_at: datetime
    consent_required: bool
    policy_version: str
