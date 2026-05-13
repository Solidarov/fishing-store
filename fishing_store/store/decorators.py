from functools import wraps
from django.core.exceptions import PermissionDenied


def not_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin_member:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
