from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def normalize_email(value: str) -> str:
    """Strip whitespace and lowercase so login/register match reliably."""
    return value.strip().lower()


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 64:
            raise ValueError("Имя пользователя: 3–64 символа")
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError("Имя пользователя: только буквы, цифры, _ и .")
        return v

    @field_validator("email")
    @classmethod
    def email_normalize(cls, v: EmailStr) -> str:
        return normalize_email(str(v))

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть не короче 8 символов")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def email_normalize(cls, v: EmailStr) -> str:
        return normalize_email(str(v))


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть не короче 8 символов")
        return v


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
