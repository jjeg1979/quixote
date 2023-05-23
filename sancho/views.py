# Python imports
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Django imports
from django.http import HttpResponse
from django.views.generic import ListView, View, TemplateView
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

# Project imports
from .models import Backtest, Metrics
from .src.parser.btgenbox import BtGenbox
from .src.parser.btmetrics import BtMetrics, DEC_PREC


class About(TemplateView):
    template_name = 'sancho/about.html'
    

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
            
            inicio = datetime.now()
            for bt in backtests:
                # Guardamos el archivo en el directorio uploads
                
                ruta_bt = Path(settings.MEDIA_ROOT)/Path(bt.name)
                with open(ruta_bt, "wb+") as dest:
                    for chunk in bt.chunks():
                        dest.write(chunk)
                
                                # Create BtGenbox object y BtMetrics
                bt_gbx = BtGenbox(Path(settings.MEDIA_ROOT), bt.name)
                bt_mts = BtMetrics(bt_gbx)
                
                # Creamos los objetos correspondientes a los modelos
                
                # btname = bt_gbx.name + bt_gbx.from_period_to_text(bt_gbx.period)
                backtest = Backtest(
                    user=user,
                    name=bt_gbx.name,
                    optimization=opti_number,
                    period_type=bt_gbx.period,
                    symbol=bt_gbx.symbol,
                    timeframe=timeframe,
                    ordertype=bt_gbx.ordertype,
                    date_from=bt_start,
                    date_to=bt_end,
                )
                
                bts.append(backtest)
                
                valido = True if bt_mts.valid == 'Y' else False
                days, hours, minutes, seconds = bt_mts.calculate_time_in_market()                
                time_in_market = timedelta(days=days, hours=hours, \
                        minutes=minutes, seconds=seconds)
                op_promedio = bt_gbx.operations.Duration.sum() / bt_gbx.operations.shape[0]
                avg_days = op_promedio.days
                avg_hours = (op_promedio - timedelta(days=avg_days)).seconds // 3600
                avg_minutes = (op_promedio - timedelta(days=avg_days, hours=avg_hours)).seconds //60
                metrics = Metrics(
                    backtest=backtest,
                    is_valid=valido,                    
                    profit=bt_mts.gross_profit(),
                    loss=bt_mts.gross_loss(),
                    num_ops=bt_mts.num_ops,
                    pf=bt_mts.calculate_pf(),
                    rf=bt_mts.calculate_rf(),
                    dd=Decimal(bt_mts.drawdown().min()).quantize(Decimal(DEC_PREC)),
                    ep=bt_mts.esp(),
                    kratio=bt_mts.calculate_kratio(),
                    max_losing_strike=bt_mts.get_max_losing_strike(),
                    max_winning_strike=bt_mts.get_max_winning_strike(),
                    avg_losing_strike=bt_mts.get_avg_losing_strike(),
                    avg_winning_strike=bt_mts.get_avg_winning_strike(),
                    max_lots=bt_gbx.operations.Volume.max(),
                    min_lots=bt_gbx.operations.Volume.min(),
                    max_exposure=Decimal(max(bt_mts.exposures()[1])).quantize(Decimal(DEC_PREC)),
                    time_in_market=time_in_market,
                    pct_winner=Decimal(bt_mts.pct_win()).quantize(Decimal(DEC_PREC)),
                    closing_days=bt_mts.calculate_closing_days(),
                    sqn=bt_mts.calculate_sqn(),
                    sharpe_ratio=bt_mts.calculate_sharpe(),
                    best_operation_pips=int(bt_mts.best_operation()[0]),
                    best_operation_datetime=bt_mts.best_operation()[1], 
                    worst_operation_pips=int(bt_mts.worst_operation()[0]),
                    worst_operation_datetime=bt_mts.worst_operation()[1],
                    avg_win=bt_mts.calculate_avg_win(),
                    avg_loss=bt_mts.calculate_avg_loss(),
                    total_bt_duration=bt_end-bt_start,
                    avg_op_duration=timedelta(days=avg_days, hours=avg_hours, minutes=avg_minutes),
                    longest_op_duration=bt_gbx.operations.Duration.max(),
                    shortest_op_duration=bt_gbx.operations.Duration.min(),
                )
                mts.append(metrics)

                bt_gbx = None
                bt_mts = None
                backtest = None
                metrics = None                
                os.remove(ruta_bt)
        
        if settings.DEBUG:        
            print(f'Duración del procesamiento de backtest {(datetime.now() - inicio).minutes} minutos')
        self.create_registers(bts, mts)
                    
        context = {
            'bts': bts,
            'mts': mts,
        }
        
        breakpoint()
        # Enviar datos al formulario de salida
        return render(request, 'sancho/backtests/processed.html', context=context)
    
    @transaction.atomic
    def create_registers(self, bts: list, mts: list) -> None:
        Backtest.objects.bulk_create(bts)
        Metrics.objects.bulk_create(mts)
        


class ProcessedBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/processed.html"