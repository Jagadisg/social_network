from loguru import logger
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError


def save_session(request : HttpRequest, user: dict):
    for key, value in user.items():
        request.session[key] = value
    return None


def save_object_into_database(query_object, name: str):
    try:
        query_object.save()
    except ValidationError as e:
        logger.error(f"Validation Error: {e}")
        return {"message": f"Validation Error: {e}", "status": 403}
    except IntegrityError as e:
        logger.error(f"Integrity Error: {e}")
        return {"message": f"Integrity Error: {e}", "status": 403}
    except OperationalError as e:
        logger.error(f"Operational Error: {e}")
        return {"message": f"Operational Error: {e}", "status": 403}
    except Exception as e:
        logger.error(f"Unable to save {name}: {e}")
        return {
            "message": f"Unable to save {name}: {e}",
            "status": 500,
        }
    return None