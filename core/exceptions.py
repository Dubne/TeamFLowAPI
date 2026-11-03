from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):

    if isinstance(exc, DjangoValidationError):

        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        else:
            detail = exc.messages

        exc = DRFValidationError(detail=detail)

    return exception_handler(exc, context)