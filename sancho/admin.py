# Django imports
from django.contrib import admin
from django import forms 
#from durationwidget.widgets import TimeDurationWidget

# Project imports
from .models import Backtest, Metrics

# clase para incluir el widget de duración de tiempo
'''
class MetricsAdminForm(forms.ModelForm):
   duration = forms.DurationField(widget=TimeDurationWidget(
       show_days=True,
       show_hours=True,
       show_minutes=True,
       show_secons=True), required=False)
   
   class Meta:
        model = Metrics
'''

@admin.register(Backtest)
class BacktestAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'timeframe', 'ordertype', 'family', 'created']
    list_filter = ['timeframe', 'symbol', 'ordertype', 'family', 'name']
    search_fields = ['symbol', 'family']
    date_hierarchy = 'created'
    ordering = ['timeframe', 'symbol', 'name', 'ordertype', 'family']

@admin.register(Metrics)
class MetricsAdmin(admin.ModelAdmin):
    #form = MetricsAdminForm    
    list_display = ['backtest', 'kratio', 'rf', 'max_exposure', 'closing_days', 'num_ops'] 
    list_filter = ['kratio', 'rf', 'closing_days']
    search_filter = ['kratio', 'rf']    
    ordering = ['-kratio', '-rf', '-closing_days']