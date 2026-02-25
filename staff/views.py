from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, FormView, UpdateView, DeleteView
from django.urls import reverse
from django.db import transaction
from django import forms
from django.contrib.auth import get_user_model

from staff.models import Staff
from stores.models import Store
from staff.forms import StaffCreateForm
User = get_user_model()


# -----------------------------
# Mixins
# -----------------------------
class StoreContextMixin:
    """Provides get_store() to get current store from URL safely."""
    def get_store(self):
        return get_object_or_404(Store, pk=self.kwargs["store_id"])


class StoreOwnerRequiredMixin(StoreContextMixin):
    """Ensures only the store owner can manage staff."""
    def dispatch(self, request, *args, **kwargs):
        store = self.get_store()
        if request.user != store.owner:
            raise PermissionDenied("Only store owner can manage staff.")
        return super().dispatch(request, *args, **kwargs)


# -----------------------------
# Views
# -----------------------------
class StaffListView(StoreOwnerRequiredMixin, ListView):
    model = Staff
    template_name = "dashboard/staff/staff_list.html"
    context_object_name = "staff_members"

    def get_queryset(self):
        # Only show staff belonging to this store
        return Staff.objects.filter(store=self.get_store())


class StaffCreateView(StoreOwnerRequiredMixin, FormView):
    template_name = "dashboard/staff/staff_create.html"
    form_class = StaffCreateForm

    def form_valid(self, form):
        store = self.get_store()
        email = form.cleaned_data["email"]

        # Prevent duplicate users
        if User.objects.filter(email=email).exists():
            form.add_error("email", "A user with this email already exists.")
            return self.form_invalid(form)

        # Use transaction to prevent partial creation
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )

            Staff.objects.create(
                user=user,
                store=store,
                role=form.cleaned_data["role"]
            )

        return redirect("staff:list", store_id=store.id)


class StaffUpdateView(StoreOwnerRequiredMixin, UpdateView):
    model = Staff
    fields = ["role"]
    template_name = "dashboard/staff/staff_update.html"

    def get_queryset(self):
        # Restrict update to staff of this store only
        return Staff.objects.filter(store=self.get_store())

    def get_success_url(self):
        return reverse("staff:list", kwargs={"store_id": self.get_store().id})


class StaffDeleteView(StoreOwnerRequiredMixin, DeleteView):
    model = Staff
    template_name = "dashboard/staff/staff_confirm_delete.html"

    def get_queryset(self):
        # Restrict deletion to staff of this store only
        return Staff.objects.filter(store=self.get_store())

    def get_success_url(self):
        return reverse("staff:list", kwargs={"store_id": self.get_store().id})