import json
from typing import List, Dict, Any
from app.core.redis import get_redis

class SessionService:
    TTL = 86400  # 24 hours

    @staticmethod
    async def get_history(session_id: str, user_id: str) -> List[Dict[str, Any]]:
        redis = await get_redis()
        key = f"session:{user_id}:{session_id}"
        data = await redis.lrange(key, 0, -1)
        if not data:
            return []
        
        # Redis lrange returns oldest first if we append, but let's parse
        history = []
        for item in data:
            history.append(json.loads(item))
        return history

    @staticmethod
    async def append_message(session_id: str, user_id: str, role: str, content: str, timestamp: str):
        redis = await get_redis()
        key = f"session:{user_id}:{session_id}"
        
        # Track session ID in a set for listing
        index_key = f"user_sessions:{user_id}"
        await redis.sadd(index_key, session_id)
        await redis.expire(index_key, SessionService.TTL)

        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        await redis.rpush(key, json.dumps(message))
        await redis.expire(key, SessionService.TTL)

    @staticmethod
    async def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
        redis = await get_redis()
        index_key = f"user_sessions:{user_id}"
        session_ids = await redis.smembers(index_key)
        
        sessions = []
        for sid in session_ids:
            # Fetch last message for a preview title
            key = f"session:{user_id}:{sid}"
            last_msg_json = await redis.lindex(key, -1)
            if last_msg_json:
                last_msg = json.loads(last_msg_json)
                sessions.append({
                    "id": sid,
                    "last_message": last_msg["content"][:40] + "...",
                    "timestamp": last_msg["timestamp"]
                })
        
        # Sort by timestamp descending
        sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        return sessions

    @staticmethod
    async def save_portfolio(user_id: str, holdings: List[Dict[str, Any]]):
        redis = await get_redis()
        key = f"portfolio:{user_id}"
        await redis.setex(key, SessionService.TTL, json.dumps(holdings))

session_service = SessionService()
