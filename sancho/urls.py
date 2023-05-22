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
    path(
        "backtests/process.html", views.ProcessBacktests.as_view(), name="process_backtests"
    ),
    path(
        "backtests/processed.html", views.ProcessedBacktests.as_view(), name="processed_backtests"
    ),    
]
