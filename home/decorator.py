from functools import wraps

from loguru import logger
from rest_framework.response import Response


def authenticate_user_session(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if "sessionid" in request.COOKIES.keys():
            if request.COOKIES["sessionid"] != request.session.session_key:
                logger.warning("Incorrect session ID.")
                return Response({"message": "Incorrect session ID."}, status=401)
        else:
            logger.warning("User is not logged in.")
            return Response({"message": "User is not logged in."}, status=401)

        response = view_func(request, *args, **kwargs)
        return response

    return wrapped_view