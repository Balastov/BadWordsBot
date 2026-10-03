from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.e2e import decode_public_key_b64
from app.core.e2e_users import get_direct_chat_partner_ids
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import ChangePasswordBody, UserOut
from app.ws.hub import manager

router = APIRouter(prefix="/users", tags=["users"])

BACKUP_PREFIX = "ENC_BACKUP:v1:"
MAX_BACKUP_LEN = 16_384


class UploadKeyBody(BaseModel):
    public_key: str  # base64-encoded X25519 public key (32 bytes)
    force: bool = False


class RotateKeyBody(BaseModel):
    password: str = Field(min_length=8)
    public_key: str


class KeyBackupBody(BaseModel):
    backup: str = Field(min_length=len(BACKUP_PREFIX) + 1, max_length=MAX_BACKUP_LEN)


class PublicKeyOut(BaseModel):
    user_id: str
    public_key: str | None
    public_key_updated_at: datetime | None = None


class KeyBackupOut(BaseModel):
    backup: str | None


async def _set_public_key_and_notify(
    current_user: User,
    public_key: str,
    db: AsyncSession,
    *,
    force_changed: bool,
) -> PublicKeyOut:
    try:
        decode_public_key_b64(public_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    key_changed = force_changed or (
        current_user.public_key is not None and current_user.public_key != public_key
    )

    current_user.public_key = public_key
    if key_changed or current_user.public_key_updated_at is None:
        current_user.public_key_updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_user)

    if key_changed:
        partner_ids = await get_direct_chat_partner_ids(current_user.id, db)
        await manager.broadcast_to_users(
            partner_ids,
            {
                "type": "key_changed",
                "user_id": current_user.id,
                "public_key": current_user.public_key,
                "updated_at": current_user.public_key_updated_at.isoformat(),
            },
        )

    return PublicKeyOut(
        user_id=current_user.id,
        public_key=current_user.public_key,
        public_key_updated_at=current_user.public_key_updated_at,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("/me/password")
async def change_password(
    body: ChangePasswordBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Смена пароля аккаунта (нужен текущий пароль)."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный текущий пароль")

    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="Новый пароль должен отличаться от текущего")

    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}


@router.put("/me/key", response_model=PublicKeyOut)
async def upload_public_key(
    body: UploadKeyBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Загружает публичный X25519-ключ пользователя (используется для E2E шифрования)."""
    if (
        current_user.public_key
        and current_user.public_key != body.public_key
        and not body.force
    ):
        raise HTTPException(
            status_code=409,
            detail="Public key already set. Use force=true to rotate.",
        )

    return await _set_public_key_and_notify(
        current_user,
        body.public_key,
        db,
        force_changed=bool(
            current_user.public_key and current_user.public_key != body.public_key
        ),
    )


@router.post("/me/key/rotate", response_model=PublicKeyOut)
async def rotate_public_key(
    body: RotateKeyBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Ротация публичного ключа с подтверждением паролем аккаунта."""
    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный пароль")

    return await _set_public_key_and_notify(
        current_user,
        body.public_key,
        db,
        force_changed=True,
    )


@router.put("/me/key-backup", response_model=KeyBackupOut)
async def save_key_backup(
    body: KeyBackupBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Сохраняет зашифрованную резервную копию ключей (сервер хранит только ciphertext)."""
    if not body.backup.startswith(BACKUP_PREFIX):
        raise HTTPException(status_code=422, detail="Invalid backup format")

    current_user.key_backup = body.backup
    await db.commit()
    return KeyBackupOut(backup=current_user.key_backup)


@router.get("/me/key-backup", response_model=KeyBackupOut)
async def get_key_backup(current_user: Annotated[User, Depends(get_current_user)]):
    return KeyBackupOut(backup=current_user.key_backup)


@router.get("/{user_id}/key", response_model=PublicKeyOut)
async def get_public_key(
    user_id: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Возвращает публичный ключ пользователя для установки E2E-сессии."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return PublicKeyOut(
        user_id=user.id,
        public_key=user.public_key,
        public_key_updated_at=user.public_key_updated_at,
    )


@router.get("/search", response_model=list[UserOut])
async def search_users(
    q: Annotated[str, Query(min_length=2)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User)
        .where(User.username.ilike(f"%{q}%"), User.id != current_user.id)
        .limit(20)
    )
    return result.scalars().all()
