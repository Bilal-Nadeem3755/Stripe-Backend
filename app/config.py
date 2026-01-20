from dotenv import load_dotenv
import os
from typing import Final

load_dotenv()

def require_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"❌ Environment variable '{key}' is missing")
    return value

# Mongo
MONGO_URI: Final[str] = require_env("MONGO_URI")
DB_NAME: Final[str] = require_env("DB_NAME")

# Stripe
STRIPE_SECRET_KEY: Final[str] = require_env("STRIPE_SECRET_KEY")

# JWT
JWT_SECRET_KEY: Final[str] = require_env("JWT_SECRET_KEY")
JWT_ALGORITHM: Final[str] = require_env("JWT_ALGORITHM")
JWT_EXPIRE_MINUTES: Final[int] = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
