from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView
from ecom.public_decorator import public
from .forms import RegisterForm


class RedirectAuthenticatedMixin:
    """Redirect authenticated users away from auth pages."""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("orders:orders_list")
        return super().dispatch(request, *args, **kwargs)


@public
class UserLoginView(RedirectAuthenticatedMixin, View):
    template_name = "accounts/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Handle "Remember Me" checkbox
            remember_me = request.POST.get("remember_me")
            if remember_me:
                request.session.set_expiry(2629743)  # 1 month
            else:
                request.session.set_expiry(0)  # Session expires when the browser is closed

            return redirect("orders:orders_list")

        return render(request, self.template_name, {"form": form})

@public
class UserRegisterView(RedirectAuthenticatedMixin, FormView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("orders:orders_list")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

@public
class UserPasswordResetView(RedirectAuthenticatedMixin, View):
    template_name = "accounts/password_reset.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PasswordResetForm()})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": form})

@public
class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("accounts:login")
