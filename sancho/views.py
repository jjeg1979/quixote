from django.http import HttpResponse
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import FileSystemStorage

from .models import Backtest, Metrics


class ListBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/list.html"
    
    
class ProcessBacktests(View):
