from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    env: str = os.getenv("ENV", "local")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/appdb",
    )

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "FKGROZ29zE5mJdCL2_ipNgtFs6Fg3yKBCisazEq_fj9_1I7dvI1TonQyVsrHlo7A")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    token_aud: str = os.getenv("TOKEN_AUDIENCE", "notes-api")
    token_iss: str = os.getenv("TOKEN_ISSUER", "notes-api")

    # Redis / RQ
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rq_queue_name: str = os.getenv("RQ_QUEUE_NAME", "notes_summarize")

settings = Settings()
