from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister, normalize_email

router = APIRouter(prefix="/auth", tags=["auth"])


async def _find_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find user by email, tolerant of legacy mixed-case rows."""
    normalized = normalize_email(email)
    exact = await db.execute(select(User).where(User.email == normalized))
    user = exact.scalar_one_or_none()
    if user:
        return user
    # Older rows may keep mixed-case local parts; avoid MultipleResultsFound.
    legacy = await db.execute(
        select(User).where(func.lower(User.email) == normalized).limit(1)
    )
    return legacy.scalars().first()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: Annotated[AsyncSession, Depends(get_db)]):
    email = normalize_email(body.email)
    result = await db.execute(
        select(User).where(
            (func.lower(User.email) == email) | (User.username == body.username)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email или имя пользователя уже заняты",
        )

    user = User(
        username=body.username,
        email=email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _find_user_by_email(db, body.email)

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
        )

    return TokenResponse(access_token=create_access_token(user.id))
