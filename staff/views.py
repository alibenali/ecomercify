import json
from django.shortcuts import redirect
from django.views.generic import ListView, FormView, UpdateView, DeleteView
from django.urls import reverse
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from staff.models import Staff
from staff.choices import ROLE_DEFAULT_PERMISSIONS
from stores.models import Store
from staff.forms import StaffCreateForm, StaffUpdateForm

User = get_user_model()


class StaffListView(LoginRequiredMixin, ListView):
    model = Staff
    template_name = "dashboard/staff/staff_list.html"
    context_object_name = "staff_members"

    def get_queryset(self):
        qs = (
            Staff.objects.filter(store__owner=self.request.user)
            .select_related("user", "store")
            .order_by("-created_at")
        )
        store_id = self.request.GET.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stores"] = Store.objects.filter(owner=self.request.user).order_by(
            "name"
        )
        context["selected_store_id"] = self.request.GET.get("store") or ""
        context["can_manage_staff"] = True  # Owner always can
        return context


class StaffCreateView(LoginRequiredMixin, FormView):
    template_name = "dashboard/staff/staff_create.html"
    form_class = StaffCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_default_permissions_json"] = json.dumps(ROLE_DEFAULT_PERMISSIONS)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        store = form.cleaned_data["store"]
        email = form.cleaned_data["email"]

        # Ensure the current user owns the selected store
        if store.owner != self.request.user:
            form.add_error("store", "You can only add staff to your own stores.")
            return self.form_invalid(form)

        # Prevent duplicate users
        if User.objects.filter(email=email).exists():
            form.add_error("email", "A user with this email already exists.")
            return self.form_invalid(form)

        permissions = form.cleaned_data.get("permissions") or []

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
                role=form.cleaned_data["role"],
                permissions=permissions,
            )

        messages.success(self.request, f"Staff member {user.get_full_name() or email} added successfully.")
        return redirect("staff:list")


class StaffUpdateView(LoginRequiredMixin, UpdateView):
    model = Staff
    form_class = StaffUpdateForm
    template_name = "dashboard/staff/staff_update.html"

    def get_queryset(self):
        return Staff.objects.filter(store__owner=self.request.user).select_related(
            "user", "store"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_default_permissions_json"] = json.dumps(ROLE_DEFAULT_PERMISSIONS)
        return context

    def get_success_url(self):
        return reverse("staff:list")

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Staff member {self.object.user.get_full_name() or self.object.user.email} updated successfully.",
        )
        return super().form_valid(form)


class StaffDeleteView(LoginRequiredMixin, DeleteView):
    model = Staff
    template_name = "dashboard/staff/staff_confirm_delete.html"

    def get_queryset(self):
        return Staff.objects.filter(store__owner=self.request.user).select_related(
            "user", "store"
        )

    def get_success_url(self):
        return reverse("staff:list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Staff member removed successfully.")
        return super().delete(request, *args, **kwargs)