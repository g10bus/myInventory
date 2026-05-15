from functools import wraps

from django.core.exceptions import PermissionDenied


ADMIN_ACCESS_DENIED_MESSAGE = "Доступ разрешен только администраторам."
POST_ONLY_MESSAGE = "Доступ разрешен только для POST-запросов."


def ensure_administrator(user, *, message=ADMIN_ACCESS_DENIED_MESSAGE):
    if not getattr(user, "is_administrator", False):
        raise PermissionDenied(message)


def admin_required(view_func=None, *, message=ADMIN_ACCESS_DENIED_MESSAGE):
    def decorator(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            ensure_administrator(request.user, message=message)
            return func(request, *args, **kwargs)

        return wrapped

    if view_func is None:
        return decorator

    return decorator(view_func)


def post_only(view_func=None, *, message=POST_ONLY_MESSAGE):
    def decorator(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            if request.method != "POST":
                raise PermissionDenied(message)
            return func(request, *args, **kwargs)

        return wrapped

    if view_func is None:
        return decorator

    return decorator(view_func)
