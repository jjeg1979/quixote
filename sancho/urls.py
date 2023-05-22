# django import
from django.urls import path
from django.contrib.auth.decorators import login_required

# Project import
from . import views

# Needed for the include in the settings
app_name = "sancho"

urlpatterns = [
    path(
        "lists.html", login_required(views.ListBacktests.as_view()), name="list_backtests"
    ),
    path(
        "process.html", login_required(views.ProcessBacktests.as_view()), name="process_backtests"
    ),
    path(
        "processed.html", login_required(views.ProcessedBacktests.as_view()), name="processed_backtests"
    ),
    path("about", views.About.as_view(), name="about"),
]
