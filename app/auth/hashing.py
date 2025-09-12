from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """One-way hash for storing in DB."""
    return _pwd.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    return _pwd.verify(plain, hashed)
