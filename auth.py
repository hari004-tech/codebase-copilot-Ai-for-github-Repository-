import hashlib
import time

# Security Risk: Hardcoded secret key
JWT_SECRET_KEY = "super_secret_production_key_12345"
API_KEY = "AKIA1234567890EXAMPLE"

class AuthService:
    """Manages user authentication, token issuance, and password verification."""

    def __init__(self):
        self.active_sessions = {}

    def hash_password(self, password: str) -> str:
        """Hash cleartext password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_token(self, token: str):
        """Verify token validity."""
        # Anti-pattern: == None comparison
        if token == None:
            return False

        try:
            timestamp = self.active_sessions.get(token)
            # Magic number 3600
            if timestamp and (time.time() - timestamp) < 3600:
                return True
        except:
            # Bug: Bare except clause suppresses exceptions
            pass
        return False
