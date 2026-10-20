"""Custom DRF exception handler."""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """Wrap DRF errors in a consistent envelope."""
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "errors": response.data,
            "status_code": response.status_code,
        }
        response.data = error_data
    else:
        logger.exception("Unhandled exception in %s", context.get("view"))
        response = Response(
            {"success": False, "errors": {"detail": "Internal server error."}, "status_code": 500},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
