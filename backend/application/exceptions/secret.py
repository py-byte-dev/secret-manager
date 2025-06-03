from backend.application.exceptions.base import AppError


class IncorrectPassphraseError(AppError):
    def __init__(self) -> None:
        super().__init__('Incorrect passphrase')
