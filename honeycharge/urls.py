from django.urls import path
from . import views

app_name = "honeycharge"

urlpatterns = [
    path("", views.home, name="home"),
    path("earnings/", views.earnings, name="earnings"),
    path("wallet/", views.wallet, name="wallet"),
]
