from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that enforces login for all views by default,
    unless a view is marked with the @public decorator.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if the view is a class-based view (CBV)
        if hasattr(view_func, 'view_class'):  
            view_class = view_func.view_class
            if hasattr(view_class, 'is_public') and view_class.is_public:
                return None  # Allow access

        # If it's a function-based view (FBV), check for is_public attribute
        if hasattr(view_func, 'is_public') and view_func.is_public:
            return None  # Allow access

        # Require login for all other views
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:login'))  # Redirect to login page

        return None
