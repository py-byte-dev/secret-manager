import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from backend.application import interfaces


class EncryptionService(interfaces.EncryptionService):
    def __init__(self, secret_key: bytes) -> None:
        self._secret_key = secret_key

    def encrypt(self, plaintext: str) -> bytes:
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self._secret_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        plaintext_bytes = plaintext.encode('utf-8')
        padding_length = 16 - len(plaintext_bytes) % 16
        padded = plaintext_bytes + b'\0' * padding_length
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        raw = base64.b64decode(ciphertext)
        iv = raw[:16]
        cipher = Cipher(algorithms.AES(self._secret_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(raw[16:]) + decryptor.finalize()
        return plaintext.rstrip(b'\0')
