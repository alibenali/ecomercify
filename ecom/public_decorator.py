from functools import wraps
from django.http import HttpResponseForbidden

def public(view_func):
    """
    A decorator to mark a view as public (accessible without login).
    """
    view_func.is_public = True
    return view_func
