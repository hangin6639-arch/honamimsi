from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("briefing/", views.generate_briefing, name="briefing"),
]
