# Python imports
import os
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Django imports
from django.http import HttpResponse
from django.views.generic import ListView, View, TemplateView
from django.shortcuts import render, get_object_or_404, redirect
# from django.core.files.storage import FileSystemStorage
from django.conf import settings
#from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Case, CharField, Value, When

# Project imports
from .models import Backtest, Metrics
from .src.parser.btgenbox import BtGenbox, BtPeriods, BtOrderType
from .src.parser.btmetrics import BtMetrics, DEC_PREC


class About(TemplateView):
    template_name = 'sancho/about.html'
    

# Vista para ver el listado de backtests
class ListBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/list.html"
    context_object_name = 'bts'
    
    
    '''def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Acceder al nombre del campo ordertype usando get_ordertype_display()
        for bt in context['bts']:
            breakpoint()
       
            match bt.ordertype:
                case BtOrderType.BUY:
                    bt.ordertype_display = 'Buy'
                case BtOrderType.SELL:
                    bt.ordertype_display = 'Sell'
                case BtOrderType.BOTH:
                    bt.ordertype_display = 'Buy/Sell'

            match bt.period_type:
                case BtPeriods.IS:
                    bt.periodtype_display = 'IS'
                case BtPeriods.OS:
                    bt.periodtype_display = 'OS'
                case BtPeriods.ISOS:
                    bt.periodtype_display = 'ISOS'
                    
            bt.timeframe_display = bt.get_timeframe_display()
            bt.family_display = bt.get_family_display()
            
        return context'''
    
    
    def get_queryset(self):        
        queryset = super().get_queryset().filter(period_type=BtPeriods.ISOS)       
        
        # Fine tune output
        queryset = queryset.annotate(
                ordertype_display=Case(
            When(ordertype=BtOrderType.BUY, then=Value('Buy')),
            When(ordertype=BtOrderType.SELL, then=Value('Sell')),
            When(ordertype=BtOrderType.BOTH, then=Value('Buy/Sell')),
            output_field=CharField(),
            ),
        period_type_display=Case(
            When(period_type=BtPeriods.IS, then=Value('IS')),
            When(period_type=BtPeriods.OS, then=Value('OS')),
            When(period_type=BtPeriods.ISOS, then=Value('ISOS')),
            output_field=CharField(),
            ),
        )

        for bt in queryset:    
            bt.timeframe_display = bt.get_timeframe_display()
            bt.family_display = bt.get_family_display()
                       
        return queryset
    

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
            
            bts = [] # Store GenboxBacktest model
            mts = [] # Store Metrics model
            gbx = [] # Store BtGenbox
            mtx = [] # Store BtMetrics
            
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
                gbx.append(bt_gbx)
                mtx.append(bt_mts)
                
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
                              
                os.remove(ruta_bt)
        
        if settings.DEBUG:        
            print(f'Duración del procesamiento de backtest {(datetime.now() - inicio).seconds} segundos')
        self.create_registers(bts, mts)
        
        # Create lists to pass formated data to the template
        mt_data = []
        for mt in mtx:
            mt_data.append({
                'name': mt.bt.name,
                'optimization': opti_number,
                'symbol': mt.bt.symbol,
                'ordertype_text': mt.bt.from_ordertype_to_text(mt.bt.ordertype),
                'period_text': mt.bt.from_period_to_text(mt.bt.period),
                'timeframe': timeframe,
                'valid': mt.valid
            })           
        context = {
            'bts': gbx,
            'num_periods': len(bts),
            'num_bts': len(bts) / 3,
            'timeframe': timeframe,
            'mts': mt_data,
        }        
        
        # Enviar datos al formulario de salida
        return render(request, 'sancho/backtests/processed.html', context=context)
    
    @transaction.atomic
    def create_registers(self, bts: list, mts: list) -> None:
        Backtest.objects.bulk_create(bts)
        Metrics.objects.bulk_create(mts)
        


class ProcessedBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/processed.html"
    
    
def export_backtests(request):
    breakpoint()
    bts = Backtest.valid.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content Disposition'] = 'attachment; filename="backtests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Optimization', 'Symbol', 'Order Type,', 'TimeFrame', 'Source'])
    
    for bt in bts:
        writer.writerow([bt.name, bt.optimization, bt.symbol, bt.ordertype, bt.timeframe, bt.family])

    return response
                            
    
    