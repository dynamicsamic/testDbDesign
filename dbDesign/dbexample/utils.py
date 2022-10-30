from decimal import Decimal
from functools import wraps


def decimalize(fmt: str = ".2f") -> Decimal:
    """Return result as Decimal."""

    def decorator(f: callable):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            return Decimal(format(res, fmt))

        return decorated

    return decorator
