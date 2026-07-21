from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("map/", views.siting_map, name="map"),
    path("schedule/", views.schedule_view, name="schedule"),
    path("scenario/", views.scenario_comparison, name="scenario"),
]
