from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.utils import timezone

# Project imports


# Create your own managers here
class GenboxBacktest(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(family=Backtest.Source.GENBOX)


class ProfitableBacktests(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter((Metrics.profit - Metrics.loss) > 0.0)


class ValidBacktests(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(metrics__is_valid = True,
                                             period_type = Backtest.PeriodType.ISOS)


# Backtest model
class Backtest(models.Model):
    # Class to hole the different sources for the backtest
    class Source(models.TextChoices):
        GENBOX = "GBX", "Genbox"
        METATRADER4 = "MT4", "Metatrader4"
        METATRADER5 = "MT5", "Metatrader5"
        STATEMENT = "STM", "Statement"
        UPLOADED = "UP", "Uploaded From File"

    # Clase que contiene una enumeración para los pares de divisas
    class ForexPair(models.TextChoices):
        AUDCAD = "ACD", "AUDCAD"
        AUDCHF = "ACF", "AUDCHF"
        AUDJPY = "AJ", "AUDJPY"
        AUDNZD = "AN", "AUDNZD"
        CADCHF = "CDCF", "CADCHF"
        CADJPY = "CDJ", "CADJPY"
        CHFJPY = "CFJ", "CHFJPY"
        EURAUD = "EA", "EURAUD"
        EURCAD = "ECD", "EURCAD"
        EURCHF = "ECF", "EURCHF"
        EURJPY = "EJ", "EURJPY"
        EURNZD = "EN", "EURNZD"
        EURUSD = "EU", "EURUSD"
        GBPAUD = "GA", "GBPAUD"
        GBPCAD = "GCD", "GBPCAD"
        GBPCHF = "GCF", "GBPCHF"
        GBPJPY = "GJ", "GBPJPY"
        GPBUSD = "GU", "GBPUSD"
        NZDCAD = "NCD", "NZDCAD"
        NZDCHF = "NCF", "NZDCHF"
        NZDUSD = "NU", "NZDUSD"
        USDCAD = "UCD", "USDCAD"
        USDCHF = "UCF", "USDCHF"
        USDJPY = "UJ", "USDJPY"

    class TimeFrame(models.TextChoices):
        M1 = "M1", "M1"
        M5 = "M5", "M5"
        M15 = "M15", "M15"
        M30 = "M30", "M30"
        H1 = "H1", "H1"
        H4 = "H4", "H4"
        D1 = "D1", "D1"
        W = "W", " W"
        M = "M", "M"

    class OrderType(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"
        BOTH = "BUY&SELL", "Buy and Sell"

    # Clase que contiene los diferentes periodos
    class PeriodType(models.TextChoices):
        IS = "IS", "In Sample"
        OS = "OS", "Out of Sample"
        ISOS = "ISOS", "ALL"

    # Campos del modelo Backtest
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=150)
    
    optimization = models.IntegerField()

    period_type = models.CharField(
        max_length=4, choices=PeriodType.choices, default=PeriodType.ISOS
    )

    initial_balance = models.DecimalField(max_digits=15, decimal_places = 2, default=10000)

    symbol = models.CharField(
        max_length=6, choices=ForexPair.choices, default=ForexPair.EURUSD
    )

    ordertype = models.CharField(
        max_length=8, choices=OrderType.choices, default=OrderType.BOTH
    )

    timeframe = models.CharField(
        max_length=3, choices=TimeFrame.choices, default=TimeFrame.H4
    )
    family = models.CharField(
        max_length=12, choices=Source.choices, default=Source.GENBOX
    )

    created = models.DateTimeField(default=timezone.now)
    date_from = models.DateField(default=timezone.now)
    date_to = models.DateField(default=timezone.now)

    objects = models.Manager()  # Default Manager
    genboxbt = GenboxBacktest()  # Custom Manager
    valid = ValidBacktests()    # Custom Manager

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]
        unique_together = ('name', 'optimization', 'period_type')

    def __str__(self) -> str:
        return f"""Backtest: {self.name.split()[0]} for pair: {self.symbol} 
                    and period: {self.period_type}"""


# Metrics model
class Metrics(models.Model):
    # Campos del modelo Metrics
    # Este campo relaciona el modelo Backtest con el modelo Metrics
    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE)   

    # Aquí empiezan los campos primitivos  

    is_valid = models.BooleanField()
    profit = models.DecimalField(max_digits=15, decimal_places=4)
    loss = models.DecimalField(max_digits=15, decimal_places=4)
    num_ops = models.PositiveIntegerField()

    pf = models.DecimalField(max_digits=15, decimal_places=4)
    rf = models.DecimalField(max_digits=15, decimal_places=4)
    dd = models.DecimalField(max_digits=15, decimal_places=4)
    ep = models.DecimalField(max_digits=15, decimal_places=4)

    kratio = models.DecimalField(max_digits=15, decimal_places=4)
    max_losing_strike = models.PositiveIntegerField()
    max_winning_strike = models.PositiveIntegerField()
    avg_losing_strike = models.PositiveIntegerField()
    avg_winning_strike = models.PositiveIntegerField()
    max_lots = models.DecimalField(max_digits=15, decimal_places=4)
    min_lots = models.DecimalField(max_digits=15, decimal_places=4)
    max_exposure = models.DecimalField(max_digits=15, decimal_places=4)
    time_in_market = models.DurationField()
    pct_winner = models.DecimalField(max_digits=15, decimal_places=4)
    closing_days = models.PositiveIntegerField()
    sqn = models.DecimalField(max_digits=15, decimal_places=4)
    sharpe_ratio = models.DecimalField(max_digits=15, decimal_places=4)
    best_operation_pips = models.IntegerField()
    best_operation_datetime = models.DateTimeField()
    worst_operation_pips = models.IntegerField()
    worst_operation_datetime = models.DateTimeField()
    avg_win = models.DecimalField(max_digits=15, decimal_places=4)
    avg_loss = models.DecimalField(max_digits=15, decimal_places=4)
    total_bt_duration = models.DurationField()
    avg_op_duration = models.DurationField()
    longest_op_duration = models.DurationField()
    shortest_op_duration = models.DurationField()

    objects = models.Manager()
    profitable = ProfitableBacktests()    

    class Meta:
        ordering = ["-kratio", "-rf", "max_exposure", "closing_days", "-num_ops"]
        indexes = [models.Index(fields=["-kratio"])]

    def __str__(self):
        valido = 'Sí' if self.is_valid is True else 'No'
        return f"""
                Backtest main metrics: 
                ¿Valida?: {valido},
                kratio: {self.kratio}, Recuperation Factor: {self.rf}
                Max. exposure: {self.max_exposure}, Closing Days: {self.closing_days}
                Num. Ops: {self.num_ops}
                """
