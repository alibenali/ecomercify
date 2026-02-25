from django.urls import path
from staff import views

app_name = "staff"

urlpatterns = [
    # List all staff for a specific store
    path("store/<int:store_id>/", views.StaffListView.as_view(), name="list"),

    # Create a new staff member for a store
    path("store/<int:store_id>/create/", views.StaffCreateView.as_view(), name="create"),

    # Update a staff member's role
    path(
        "store/<int:store_id>/update/<int:pk>/",
        views.StaffUpdateView.as_view(),
        name="update"
    ),

    # Delete a staff member
    path(
        "store/<int:store_id>/delete/<int:pk>/",
        views.StaffDeleteView.as_view(),
        name="delete"
    ),
]