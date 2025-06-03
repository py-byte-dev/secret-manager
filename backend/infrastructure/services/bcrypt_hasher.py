import bcrypt

from backend.application import interfaces


class BcryptHasher(interfaces.BcryptHasher):
    def hash(self, raw_data: str) -> bytes:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(raw_data.encode(), salt)

    def verify(self, raw_data: bytes, hashed_data: bytes) -> bool:
        return bcrypt.checkpw(raw_data, hashed_data)
