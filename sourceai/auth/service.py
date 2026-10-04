# sourceai/auth/service.py
import asyncio
import uuid
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from sourceai.auth.models import TokenResponse, UserCreate, UserLogin, UserResponse
from sourceai.auth.password import hash_password, verify_password
from sourceai.storage.postgres import PostgresStorage

# JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")

# will not be accessable without a  real jwt secret no default / production
JWT_SECRET = os.environ["JWT_SECRET"]
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_secret must be at least 32 characters long")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

ACCESS = 'access'
REFRESH = 'refresh'

DUMMY_HASH = hash_password('dummy-password-for-timing')

# normalize the email addresses
def _normalize_email(email: str) -> str:
    return email.strip().lower()

# shared decoder for get_current_user and refresh_token
def decode_token(token: str, expected_type: str) -> dict:
    
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={'require': ['exp', 'sub', 'type']},
    )

    if payload['type'] != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: {payload['type']}")

    return payload
        
        
class AuthService:
    def __init__(self):
        self.db = PostgresStorage()

    # register a new user
    async def register(self, user_data: UserCreate) -> UserResponse:
        await self.db.connect()
        # email
        email = _normalize_email(user_data.email)
        # password(hashed) async to avoid blocking the event loop
        hashed = await asyncio.to_thread(hash_password, user_data.password)
        # user_id
        user_id = str(uuid.uuid4())

        async with self.db.pool.acquire() as conn:
            # check if the email is already in use
            row = await conn.fetchrow(
                """
                INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at, is_admin, is_active)
                VALUES ($1, $2, $3, $4, NOW(), NOW(), FALSE, TRUE)
                RETURNING id, email, full_name, created_at, is_active
                
                """,
                user_id, email, hashed, user_data.full_name,
            )
        return UserResponse(**dict(row))
        # if row is None:
        #     raise ValueError("Email already in use")
        # # if the email is already in use
        # return UserResponse(**dict(row))



    # login a user
    async def login(self, credentials: UserLogin) -> TokenResponse:
        await self.db.connect()

        #email
        email = _normalize_email(credentials.email)

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, password_hash, is_active FROM users "
                " WHERE email = $1 ORDER BY created_at LIMIT 1 ",
                email,
            )

        hashed = row['password_hash'] if row else DUMMY_HASH
        ok = await asyncio.to_thread(verify_password, credentials.password, hashed)

        if not row or not ok or not row["is_active"]:
            raise ValueError('invalid credentials')

        return self._issue_tokens(str(row["id"]))
        
        # if not row or not verify_password(credentials.password, row["password_hash"]):
        #     raise ValueError("Invalid credentials")

        # user_id = str(row["id"])
        # access_token = self._create_token(
        #     user_id, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        # )
        # refresh_token = self._create_token(
        #     user_id,
        #     expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        #     refresh=True,
        # )
        # return TokenResponse(
        #     access_token=access_token,
        #     refresh_token=refresh_token,
        # )
    
    # issue tokens
    def _issue_tokens(self, user_id: str) -> TokenResponse:
        access_token = self._create_token(
            user_id, 
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            token_type=ACCESS
        )
        refresh_token = self._create_token(
            user_id,
            expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
            token_type=REFRESH,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )



    # create tokens for user login
    def _create_token(
        self, user_id: str, expires_in: int, token_type: str = ACCESS
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "type": token_type,
            "jti": uuid.uuid4().hex,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


    # refresh assigned tokens    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, REFRESH)
            user_id = payload["sub"]
            uuid.UUID(user_id)
        
        except (jwt.PyJWTError, ValueError):
            raise ValueError("Invalid or expired refresh token")
        
        await self.db.connect()

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                 "SELECT is_active FROM users WHERE id = $1", user_id
            )
        if row is None or not row["is_active"]:
            raise ValueError("Invalid refresh token")
 
        return self._issue_tokens(user_id)



    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Fetch a single user by primary key. Returns None if not found.

        Uses the same column list as register() so the response schema is
        identical between register, login, and /auth/me.
        """
        try:
            uuid.UUID(user_id)
        except ValueError:
            return None

        await self.db.connect()
        # try:
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, full_name, created_at, is_active
                FROM users
                WHERE id = $1
                """,
                user_id,
            )
        # except Exception:
        #     # Malformed UUID or DB error — report not-found rather than
        #     # leaking internals. The router converts this to HTTP 404.
        #     return None

        if row is None:
            return None
        return UserResponse(**dict(row))