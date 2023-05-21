# Generated by Django 4.2.1 on 2023-05-21 15:32

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Backtest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "initial_balance",
                    models.DecimalField(decimal_places=0, default=10000, max_digits=6),
                ),
                (
                    "symbol",
                    models.CharField(
                        choices=[
                            ("ACD", "AUDCAD"),
                            ("ACF", "AUDCHF"),
                            ("AJ", "AUDJPY"),
                            ("AN", "AUDNZD"),
                            ("CDCF", "CADCHF"),
                            ("CDJ", "CADJPY"),
                            ("CFJ", "CHFJPY"),
                            ("EA", "EURAUD"),
                            ("ECD", "EURCAD"),
                            ("ECF", "EURCHF"),
                            ("EJ", "EURJPY"),
                            ("EN", "EURNZD"),
                            ("EU", "EURUSD"),
                            ("GA", "GBPAUD"),
                            ("GCD", "GBPCAD"),
                            ("GCF", "GBPCHF"),
                            ("GJ", "GBPJPY"),
                            ("GU", "GBPUSD"),
                            ("NCD", "NZDCAD"),
                            ("NCF", "NZDCHF"),
                            ("NU", "NZDUSD"),
                            ("UCD", "USDCAD"),
                            ("UCF", "USDCHF"),
                            ("UJ", "USDJPY"),
                        ],
                        default="EU",
                        max_length=6,
                    ),
                ),
                (
                    "ordertype",
                    models.CharField(
                        choices=[
                            ("BUY", "Buy"),
                            ("SELL", "Sell"),
                            ("BUY&SELL", "Buy and Sell"),
                        ],
                        default="BUY&SELL",
                        max_length=8,
                    ),
                ),
                (
                    "timeframe",
                    models.CharField(
                        choices=[
                            ("M1", "One Minute"),
                            ("M5", "Five Minutes"),
                            ("M15", "Fifteen Minutes"),
                            ("M30", "Thirteen Minutes"),
                            ("H1", "One Hour"),
                            ("H4", "Four Hours"),
                            ("D1", "Daily"),
                            ("W", " Weekly"),
                            ("M", "Monthly"),
                        ],
                        default="H4",
                        max_length=3,
                    ),
                ),
                (
                    "family",
                    models.CharField(
                        choices=[
                            ("GBX", "Genbox"),
                            ("MT4", "Metatrader4"),
                            ("MT5", "Metatrader5"),
                            ("STM", "Statement"),
                            ("UP", "Uploaded From File"),
                        ],
                        default="GBX",
                        max_length=12,
                    ),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("date_from", models.DateField(default=django.utils.timezone.now)),
                ("date_to", models.DateField(default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Metrics",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_valid", models.BooleanField()),
                (
                    "period_type",
                    models.CharField(
                        choices=[
                            ("IS", "In Sample"),
                            ("OS", "Out of Sample"),
                            ("ISOS", "ALL"),
                        ],
                        default="ISOS",
                        max_length=4,
                    ),
                ),
                ("profit", models.DecimalField(decimal_places=2, max_digits=8)),
                ("loss", models.DecimalField(decimal_places=2, max_digits=8)),
                ("num_ops", models.PositiveIntegerField()),
                ("pf", models.DecimalField(decimal_places=2, max_digits=4)),
                ("rf", models.DecimalField(decimal_places=2, max_digits=4)),
                ("dd", models.DecimalField(decimal_places=2, max_digits=6)),
                ("ep", models.DecimalField(decimal_places=2, max_digits=5)),
                ("kratio", models.DecimalField(decimal_places=2, max_digits=4)),
                ("max_losing_strike", models.PositiveIntegerField()),
                ("max_winning_strike", models.PositiveIntegerField()),
                ("avg_losing_strike", models.PositiveIntegerField()),
                ("avg_winning_strike", models.PositiveIntegerField()),
                ("max_lots", models.DecimalField(decimal_places=2, max_digits=4)),
                ("min_lots", models.DecimalField(decimal_places=2, max_digits=4)),
                ("max_exposure", models.DecimalField(decimal_places=2, max_digits=4)),
                ("time_in_market", models.DurationField()),
                ("pct_winner", models.DecimalField(decimal_places=2, max_digits=4)),
                ("closing_days", models.PositiveIntegerField()),
                ("sqn", models.DecimalField(decimal_places=2, max_digits=4)),
                ("sharpe_ratio", models.DecimalField(decimal_places=2, max_digits=4)),
                ("best_operation_pips", models.IntegerField()),
                ("best_operation_datetime", models.DateTimeField()),
                ("worst_operation_pips", models.IntegerField()),
                ("worst_operation_datetime", models.DateTimeField()),
                ("avg_win", models.DecimalField(decimal_places=2, max_digits=6)),
                ("avg_loss", models.DecimalField(decimal_places=2, max_digits=6)),
                ("total_bt_duration", models.DurationField()),
                ("avg_op_duration", models.DurationField()),
                ("longest_op_duration", models.DurationField()),
                ("shortest_op_duration", models.DurationField()),
                (
                    "backtest",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sancho.backtest",
                    ),
                ),
            ],
            options={
                "ordering": [
                    "-kratio",
                    "-rf",
                    "max_exposure",
                    "closing_days",
                    "-num_ops",
                ],
            },
        ),
        migrations.AddIndex(
            model_name="backtest",
            index=models.Index(fields=["name"], name="sancho_back_name_c2aa9d_idx"),
        ),
        migrations.AddIndex(
            model_name="metrics",
            index=models.Index(
                fields=["-kratio"], name="sancho_metr_kratio_8b00c4_idx"
            ),
        ),
    ]