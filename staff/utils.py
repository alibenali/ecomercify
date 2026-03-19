"""Staff permission utilities for use across the app."""

from staff.models import Staff
from staff.choices import (
    ROLE_DEFAULT_PERMISSIONS,
    get_default_permissions_for_role,
)


def staff_has_permission(staff_member, permission):
    """
    Check if a Staff instance has a specific permission.
    Uses explicit permissions if set, otherwise falls back to role defaults.
    """
    if staff_member is None:
        return False

    perms = staff_member.permissions
    if perms is not None:
        # Explicit permissions set - use them (list of codenames)
        return permission in perms

    # Fall back to role defaults
    defaults = get_default_permissions_for_role(staff_member.role)
    return permission in defaults


def user_has_store_permission(user, store, permission):
    """
    Check if user has a permission for a store.
    Store owner has all permissions. Otherwise checks Staff membership.
    """
    if store.owner == user:
        return True

    try:
        staff = Staff.objects.get(store=store, user=user)
        return staff_has_permission(staff, permission)
    except Staff.DoesNotExist:
        return False


def user_can_manage_store(user, store):
    """Owner or staff with manage_products (manager-like). Backward compatible."""
    return user_has_store_permission(user, store, "manage_products") or store.owner == user


def user_can_access_store(user, store):
    """Owner or any staff member (basic store access / membership)."""
    if store.owner == user:
        return True
    return Staff.objects.filter(store=store, user=user).exists()
