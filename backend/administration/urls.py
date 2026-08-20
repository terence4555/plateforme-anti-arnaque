from django.urls import path
from .views import AuditListView, DashboardView

urlpatterns = [
    path("", AuditListView.as_view(), name="audit-list"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
