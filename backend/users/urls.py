from django.urls import path
from .views import CsrfView, LoginView, RegisterView, UserProfileView, LogoutView, UserPublicView

urlpatterns = [
    path('csrf/', CsrfView.as_view(), name='csrf'),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", UserProfileView.as_view(), name="profile"),
    path("<int:id_utilisateur>/", UserPublicView.as_view(), name="user-public"),
]


