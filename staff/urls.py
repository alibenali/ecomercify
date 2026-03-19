from django.urls import path
from staff import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffListView.as_view(), name="list"),
    path("create/", views.StaffCreateView.as_view(), name="create"),
    path("update/<int:pk>/", views.StaffUpdateView.as_view(), name="update"),
    path("delete/<int:pk>/", views.StaffDeleteView.as_view(), name="delete"),
]