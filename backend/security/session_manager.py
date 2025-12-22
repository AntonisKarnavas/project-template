import json
import secrets
from typing import Optional, Dict
import redis.asyncio as redis
from config import settings

class SessionManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_ttl = 86400  # 24 hours

    async def create_session(self, user_id: int, email: str, additional_data: Dict = None) -> str:
        """
        Create a new session and return the session_id.
        """
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "email": email,
            **(additional_data or {})
        }
        await self.redis.setex(
            f"session:{session_id}",
            self.session_ttl,
            json.dumps(session_data)
        )
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data if it exists and is valid.
        """
        if not session_id:
            return None
            
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
            
        return json.loads(data)

    async def refresh_session(self, session_id: str) -> bool:
        """
        Reset the TTL for an existing session.
        """
        if not session_id:
            return False
            
        # Check if exists first to avoid extending dead sessions (though expire does this too)
        # Using expire directly is efficient
        return await self.redis.expire(f"session:{session_id}", self.session_ttl)

    async def delete_session(self, session_id: str):
        """
        Revoke a session.
        """
        if session_id:
            await self.redis.delete(f"session:{session_id}")
