# Python imports
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Django imports
from django.http import HttpResponse
from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# Project imports
from .models import Backtest, Metrics
from .src.parser.btgenbox import BtGenbox
from .src.parser.btmetrics import BtMetrics

# Vista para ver el listado de backtests
class ListBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/list.html"
    
    
class ProcessBacktests(View):
    def get(self, request):
        return render(request, 'sancho/backtests/process.html')
    
    def post(self, request):
        
        if request.FILES.getlist('backtests'):            
            backtests = request.FILES.getlist('backtests')
            bt_start = datetime.strptime(request.POST.get('bt-start'), '%Y-%m-%d')
            bt_end = datetime.strptime(request.POST.get('bt-end'), '%Y-%m-%d')
            opti_number = int(request.POST.get('opti-number'))
            timeframe = request.POST.get('tfs')
            user = request.user
            
            bts = [] # Store BtGenbox
            mts = [] # Store 
            
            for bt in backtests:
                # Guardamos el archivo en el directorio uploads
                ruta_bt = Path(settings.MEDIA_ROOT/bt.name)
                with open(ruta_bt, "wb") as dest:
                    for chunk in bt.chunks():
                        dest.write(chunk)
                breakpoint()
                
                # Create BtGenbox object y BtMetrics
                bt_gbx = BtGenbox('.', bt.name)
                bt_mts = BtMetrics(bt_gbx)
                
                # Creamos los objetos correspondientes al os modelos
                backtest = Backtest(
                    user=user,
                    name=bt_gbx.name,
                    optimization=opti_number,
                    symbol=bt_gbx.symbol,
                    ordertype=bt_gbx.ordertype,
                    date_from=bt_start,
                    date_to=bt_end,
                )
                
                valido = True if bt_mts.valid == 'Y' else False
                metrics = Metrics(
                    backtest=backtest,
                    is_valid=valido,
                    period_type=bt_gbx.period,
                    profit=0,
                    loss=0,
                    num_ops=0,
                )
                
                os.remove(ruta_bt)
                
        
        return render(request, 'sancho/backtests/processed.html')
        


class ProcessedBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/processed.html"