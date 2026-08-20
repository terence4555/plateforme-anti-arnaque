from django.urls import path
from .views import VoteCreateView

urlpatterns = [path("", VoteCreateView.as_view(), name="vote-create")]
