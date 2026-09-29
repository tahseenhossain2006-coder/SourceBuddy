# sourceai/auth/service.py
import uuid
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional

from sourceai.auth.models import TokenResponse, UserCreate, UserLogin, UserResponse
from sourceai.auth.password import hash_password, verify_password
from sourceai.storage.postgres import PostgresStorage

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    def __init__(self):
        self.db = PostgresStorage()

    async def register(self, user_data: UserCreate) -> UserResponse:
        await self.db.connect()
        hashed = hash_password(user_data.password)
        user_id = str(uuid.uuid4())
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name,
                                   created_at, updated_at, is_admin, is_active)
                VALUES ($1, $2, $3, $4, NOW(), NOW(), FALSE, TRUE)
                """,
                user_id, user_data.email, hashed, user_data.full_name,
            )
            row = await conn.fetchrow(
                "SELECT id, email, full_name, created_at, is_active "
                "FROM users WHERE id = $1",
                user_id,
            )
        return UserResponse(**dict(row))

    async def login(self, credentials: UserLogin) -> TokenResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, password_hash FROM users WHERE email = $1",
                credentials.email,
            )
        if not row or not verify_password(credentials.password, row["password_hash"]):
            raise ValueError("Invalid credentials")

        user_id = str(row["id"])
        access_token = self._create_token(
            user_id, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        refresh_token = self._create_token(
            user_id,
            expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
            refresh=True,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def _create_token(
        self, user_id: str, expires_in: int, refresh: bool = False
    ) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "refresh": refresh,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = jwt.decode(
                refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
            )
            if not payload.get("refresh"):
                raise ValueError("Invalid refresh token")
            user_id = payload["sub"]
            return TokenResponse(
                access_token=self._create_token(
                    user_id, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
                ),
                refresh_token=self._create_token(
                    user_id,
                    expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                    refresh=True,
                ),
            )
        except jwt.PyJWTError:
            raise ValueError("Invalid or expired refresh token")

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Fetch a single user by primary key. Returns None if not found.

        Uses the same column list as register() so the response schema is
        identical between register, login, and /auth/me.
        """
        await self.db.connect()
        try:
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, email, full_name, created_at, is_active
                    FROM users
                    WHERE id = $1
                    """,
                    user_id,
                )
        except Exception:
            # Malformed UUID or DB error — report not-found rather than
            # leaking internals. The router converts this to HTTP 404.
            return None

        if row is None:
            return None
        return UserResponse(**dict(row))