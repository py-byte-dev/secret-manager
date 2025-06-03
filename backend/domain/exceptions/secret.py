from backend.domain.exceptions.base import DomainError


class SecretNotFound(DomainError):
    def __init__(self):
        super().__init__('Secret not found')
