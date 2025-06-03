from backend.application import exceptions as app_exceptions
from backend.domain import exceptions as domain_exceptions
from backend.presentation.api.middlewares import exceptions_handlers

EXCEPTIONS_MAPPING = {
    app_exceptions.IncorrectPassphraseError: exceptions_handlers.incorrect_passphrase_exception_handler,
    domain_exceptions.SecretNotFound: exceptions_handlers.secret_not_found_exception_handler,
}
