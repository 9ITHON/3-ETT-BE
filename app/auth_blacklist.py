# # app/auth_blacklist.py
# import redis
# import os

# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_DB = int(os.getenv("REDIS_DB", 0))
# BLACKLIST_EXPIRE = int(os.getenv("JWT_EXPIRE_SECONDS", 3600))  # 토큰 만료시간과 동일

# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# def add_to_blacklist(token: str):
#     r.setex(f"blacklist:{token}", BLACKLIST_EXPIRE, "1")

# def is_blacklisted(token: str) -> bool:
#     return r.exists(f"blacklist:{token}") == 1
