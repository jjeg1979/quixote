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
from django.http import JsonResponse

# Project imports
from .models import Backtest, Metrics
from .src.parser.btgenbox import BtGenbox, BtPeriods, BtOrderType
from .src.parser.btmetrics import BtMetrics, DEC_PREC, DEFAULT_CRITERIA


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
        queryset = super().get_queryset().filter(period_type=Backtest.PeriodType.ISOS)       
        
        # Fine tune output
        queryset = queryset.annotate(
                ordertype_display=Case(
            When(ordertype=Backtest.OrderType.BUY, then=Value('Buy')),
            When(ordertype=Backtest.OrderType.SELL, then=Value('Sell')),
            When(ordertype=Backtest.OrderType.BOTH, then=Value('Buy/Sell')),
            output_field=CharField(),
            ),
        period_type_display=Case(
            When(period_type=Backtest.PeriodType.IS, then=Value('IS')),
            When(period_type=Backtest.PeriodType.OS, then=Value('OS')),
            When(period_type=Backtest.PeriodType.ISOS, then=Value('ISOS')),
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

            total_backtests = len(backtests)
            progress_step = 100 / total_backtests
            current_progress = 0

            
            inicio = datetime.now()
            for i, bt in enumerate(backtests):
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
                
                match bt_gbx.ordertype:
                    case BtOrderType.BUY:
                        order_type_for_db = Backtest.OrderType.BUY
                    case BtOrderType.SELL:
                        order_type_for_db = Backtest.OrderType.SELL
                    case BtOrderType.BOTH:
                        order_type_for_db = Backtest.OrderType.BOTH

                match bt_gbx.period:
                    case BtPeriods.IS:
                        period_type_for_db = Backtest.PeriodType.IS
                    case BtPeriods.OS:
                        period_type_for_db = Backtest.PeriodType.OS
                    case BtPeriods.ISOS:
                        period_type_for_db = Backtest.PeriodType.ISOS

                match timeframe:
                    case 'M1':
                        tf_for_db = Backtest.TimeFrame.M1
                    case 'M5':
                        tf_for_db = Backtest.TimeFrame.M5
                    case 'M15':
                        tf_for_db = Backtest.TimeFrame.M15
                    case 'M30':
                        tf_for_db = Backtest.TimeFrame.M30
                    case 'H1':
                        tf_for_db = Backtest.TimeFrame.H1
                    case 'H4':
                        tf_for_db = Backtest.TimeFrame.H4
                    case 'D1':
                        tf_for_db = Backtest.TimeFrame.D1
                    case 'W':
                        tf_for_db = Backtest.TimeFrame.W
                    case 'M':
                        tf_for_db = Backtest.TimeFrame.M
                

                # btname = bt_gbx.name + bt_gbx.from_period_to_text(bt_gbx.period)
                backtest = Backtest(
                    user=user,
                    name=bt_gbx.name,
                    optimization=opti_number,
                    period_type=period_type_for_db,
                    symbol=bt_gbx.symbol,
                    timeframe=tf_for_db,
                    ordertype=order_type_for_db,
                    date_from=bt_start,
                    date_to=bt_end,
                )
                
                bts.append(backtest)
                
                valido = True if bt_mts.is_valid(DEFAULT_CRITERIA) == 'Y' else False
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

                 # Actualizar el progreso
                current_progress = (i + 1) * progress_step
                progress_data = {
                    'progress': int(current_progress),
                }
                self.update_progress(request, progress_data)
        
        
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
                'valid': 'Y' if valido else 'N'
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
    
    def update_progress(self, request, data):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse(data)
    
    
    @transaction.atomic
    def create_registers(self, bts: list, mts: list) -> None:
        Backtest.objects.bulk_create(bts)
        Metrics.objects.bulk_create(mts)


class ProcessedBacktests(ListView):
    model = Backtest
    template_name = "sancho/backtests/processed.html"
    
    
'''def export_backtests(request):
    
    bts = Backtest.valid.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content Disposition'] = 'attachment; filename="backtests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Optimization', 'Symbol', 'Order Type,', 'TimeFrame', 'Source'])
    
    for bt in bts:
        writer.writerow([bt.name, bt.optimization, bt.symbol, bt.ordertype, bt.timeframe, bt.family])

    return response'''


class ExportBacktests(ListView):
    model = Metrics
    context_object_name = 'mts'

    HEADER = ['#', 'Name', 'Activo', 'TF', 'Exploracion', 'Opti #', 'Set #', 'Direccion', 
                         'VALIDA?', 'PIPS', 'kratio', 'SQN', 'EP', 'DD', 'RF', 'PF', '# Ops', 'Win Ops',
                         '%w', 'Mejor Op', 'Peor Op', 'Max. Ganancia consecutiva', 'Max. Perdida consecutiva',
                         'Max. Exposicion Mercado', 'Perdida Media', 'Ganancia Media', 'Ratio', 'Dias', 
                         '% tiempo mercado', 'Tiempo medio op.', 'Op mas larga', 'Op mas corta']

    def get_queryset(self):        
        queryset = super().get_queryset().filter(backtest__period_type=Backtest.PeriodType.ISOS)       
       
        return queryset
    
    def get(self, request):
        mts = self.get_queryset().order_by('-backtest__timeframe')

        request = HttpResponse(content_type='text/csv')
        request['Content-Disposition'] = 'attachment; filename="backtests.csv"'

        writer = csv.writer(request)
        writer.writerow(self.HEADER)

        num_set = 0
        for mt in mts:
                        
            bt = mt.backtest
            win_ops = int(mt.num_ops * mt.pct_winner / 100) 
            ratio = Decimal(-(mt.avg_win / mt.avg_loss)).quantize(Decimal(DEC_PREC)) if mt.avg_loss != 0 else 10000
            valida = 'Y' if mt.is_valid else 'N'
            
            '''
            op_type = ''
            match bt.ordertype:
                case BtOrderType.BUY:
                    op_type = 'Buy'
                case BtOrderType.SELL:
                    op_type = 'Sell'
                case BtOrderType.BOTH:
                    op_type = 'Buy/Sell'
            '''
            pct_time_in_market = Decimal(mt.time_in_market * 100 / mt.total_bt_duration).quantize(Decimal(DEC_PREC))

            writer.writerow(['', bt.name, bt.symbol, bt.timeframe, '', bt.optimization, num_set, bt.ordertype.title(), 
                             valida, int(mt.profit), mt.kratio, mt.sqn, mt.ep, int(-mt.dd), mt.rf, mt.pf, mt.num_ops, win_ops,
                             mt.pct_winner, mt.best_operation_pips, mt.worst_operation_pips, mt.max_winning_strike,
                             mt.max_losing_strike, mt.max_exposure, -int(mt.avg_loss), int(mt.avg_win), ratio, mt.closing_days,
                             pct_time_in_market, mt.avg_op_duration, mt.longest_op_duration, mt.shortest_op_duration])
            num_set += 1

        return request    

                           
    
    