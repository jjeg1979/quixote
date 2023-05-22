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
        return super().get_queryset().filter((Metrics.is_valid == True))


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
        M1 = "M1", "One Minute"
        M5 = "M5", "Five Minutes"
        M15 = "M15", "Fifteen Minutes"
        M30 = "M30", "Thirteen Minutes"
        H1 = "H1", "One Hour"
        H4 = "H4", "Four Hours"
        D1 = "D1", "Daily"
        W = "W", " Weekly"
        M = "M", "Monthly"

    class OrderType(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"
        BOTH = "BUY&SELL", "Buy and Sell"

    # Campos del modelo Backtest
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100, unique=True)
    
    optimization = models.IntegerField()

    initial_balance = models.DecimalField(max_digits=6, decimal_places=0, default=10000)

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

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self) -> str:
        return f"Backtest: {self.name.split()[0]} for pair: {self.symbol}"


# Metrics model
class Metrics(models.Model):
    # Clase que contiene los diferentes periodos
    class PeriodType(models.TextChoices):
        IS = "IS", "In Sample"
        OS = "OS", "Out of Sample"
        ISOS = "ISOS", "ALL"

    # Campos del modelo Metrics
    # Este campo relaciona el modelo Backtest con el modelo Metrics
    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE)

    is_valid = models.BooleanField()

    # Aquí empiezan los campos primitivos
    period_type = models.CharField(
        max_length=4, choices=PeriodType.choices, default=PeriodType.ISOS
    )

    profit = models.DecimalField(max_digits=8, decimal_places=2)
    loss = models.DecimalField(max_digits=8, decimal_places=2)
    num_ops = models.PositiveIntegerField()

    pf = models.DecimalField(max_digits=4, decimal_places=2)
    rf = models.DecimalField(max_digits=4, decimal_places=2)
    dd = models.DecimalField(max_digits=6, decimal_places=2)
    ep = models.DecimalField(max_digits=5, decimal_places=2)

    kratio = models.DecimalField(max_digits=4, decimal_places=2)
    max_losing_strike = models.PositiveIntegerField()
    max_winning_strike = models.PositiveIntegerField()
    avg_losing_strike = models.PositiveIntegerField()
    avg_winning_strike = models.PositiveIntegerField()
    max_lots = models.DecimalField(max_digits=4, decimal_places=2)
    min_lots = models.DecimalField(max_digits=4, decimal_places=2)
    max_exposure = models.DecimalField(max_digits=4, decimal_places=2)
    time_in_market = models.DurationField()
    pct_winner = models.DecimalField(max_digits=4, decimal_places=2)
    closing_days = models.PositiveIntegerField()
    sqn = models.DecimalField(max_digits=4, decimal_places=2)
    sharpe_ratio = models.DecimalField(max_digits=4, decimal_places=2)
    best_operation_pips = models.IntegerField()
    best_operation_datetime = models.DateTimeField()
    worst_operation_pips = models.IntegerField()
    worst_operation_datetime = models.DateTimeField()
    avg_win = models.DecimalField(max_digits=6, decimal_places=2)
    avg_loss = models.DecimalField(max_digits=6, decimal_places=2)
    total_bt_duration = models.DurationField()
    avg_op_duration = models.DurationField()
    longest_op_duration = models.DurationField()
    shortest_op_duration = models.DurationField()

    objects = models.Manager()
    profitable = ProfitableBacktests()
    valid = ValidBacktests()

    class Meta:
        ordering = ["-kratio", "-rf", "max_exposure", "closing_days", "-num_ops"]
        indexes = [models.Index(fields=["-kratio"])]

    def __str__(self):
        return f"""Backtest main metrics: 

                ¿Valida?: 'Sí' if {self.is_valid} is True else 'No',
                kratio: {self.kratio}, Recuperation Factor: {self.rf}
                Max. exposure: {self.max_exposure}, Closing Days: {self.closing_days}
                Num. Ops: {self.num_ops}"""
