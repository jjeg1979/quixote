# django import
from django.urls import path

# Project import
from . import views

# Needed for the include in the settings
app_name = 'sancho'

urlpatterns = [
    #path("", views.index, name="index"),
    # path('backtest', views.bt_list, name='backtest_list'),
    #path('backtest/metrics/<int:bt_id>/', views.bt_metrics, name='backtest_metrics'),
    #path('backtest/uploadBacktests.html', views.upload_backtest, name='upload_backtests'),
    #path('class/backtest', views.BacktestListView.as_view(), name='class_backtest_list'),
    #path('backtest/process.html', views.ProcessBacktests.as_view(), name='process_backtest'),
]
