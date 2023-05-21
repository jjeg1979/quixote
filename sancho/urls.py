# django import
from django.urls import path

# Project import
from . import views

# Needed for the include in the settings
app_name = "sancho"

urlpatterns = [
    path(
        "backtests/lists.html", views.ListBacktests.as_view(), name="list_backtests"
    ),
]
