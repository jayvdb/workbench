# Generated by Django 2.2rc1 on 2019-03-25 09:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0010_auto_20190321_1448"),
        ("accruals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CutoffDate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("day", models.DateField(unique=True, verbose_name="cutoff date")),
            ],
            options={
                "ordering": ["-day"],
                "verbose_name": "cutoff date",
                "verbose_name_plural": "cutoff dates",
            },
        ),
        migrations.AlterModelOptions(
            name="accrual",
            options={
                "ordering": [
                    "invoice__project__created_at__year",
                    "invoice__project___code",
                    "invoice___code",
                ],
                "verbose_name": "accrual",
                "verbose_name_plural": "accruals",
            },
        ),
        migrations.AddField(
            model_name="accrual",
            name="cutoff_date",
            field=models.DateField(default=None, verbose_name="cutoff date"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="accrual",
            name="logbook",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="logbook",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="accrual",
            name="work_progress",
            field=models.IntegerField(
                default=0,
                help_text="Percentage of down payment invoice for which the work has already been done.",
                verbose_name="work progress",
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="accrual", unique_together={("invoice", "cutoff_date")}
        ),
        migrations.RemoveField(model_name="accrual", name="accrual"),
        migrations.RemoveField(model_name="accrual", name="month"),
    ]
