"""Staff roles and permission constants."""

ROLE_CHOICES = [
    ("manager", "Manager"),
    ("confirmation_assistant", "Confirmation Assistant"),
    ("delivery_assistant", "Delivery Assistant"),
]

# Granular permissions (store-level)
# Format: (codename, label, description)
PERMISSION_CHOICES = [
    ("manage_orders", "Manage orders", "Add, edit, delete orders"),
    ("confirm_orders", "Confirm orders", "View and confirm orders"),
    ("dispatch_orders", "Dispatch orders", "View and dispatch orders"),
    ("manage_products", "Manage products", "Add, edit, delete products and variants"),
    ("manage_landing_pages", "Manage landing pages", "Create, edit landing pages"),
    ("manage_staff", "Manage staff", "Add, edit, remove staff members"),
]

# Default permissions per role (when permissions field is empty, these apply)
ROLE_DEFAULT_PERMISSIONS = {
    "manager": [
        "manage_orders",
        "confirm_orders",
        "dispatch_orders",
        "manage_products",
        "manage_landing_pages",
        "manage_staff",
    ],
    "confirmation_assistant": [
        "confirm_orders",
    ],
    "delivery_assistant": [
        "dispatch_orders",
    ],
}


def get_permission_labels():
    """Return dict of codename -> label for template use."""
    return {p[0]: p[1] for p in PERMISSION_CHOICES}


def get_permission_descriptions():
    """Return dict of codename -> description."""
    return {p[0]: p[2] for p in PERMISSION_CHOICES}


def get_default_permissions_for_role(role):
    """Return list of permission codenames for a role."""
    return ROLE_DEFAULT_PERMISSIONS.get(role, [])
