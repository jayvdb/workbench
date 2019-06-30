# Generated by Django 2.2.2 on 2019-06-30 20:18

from django.db import migrations, models

from workbench.tools import search


class Migration(migrations.Migration):

    dependencies = [("invoices", "0011_auto_20190404_1136")]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="_fts",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.RunSQL(
            search.fts(
                "invoices_invoice", ["title", "description", "postal_address", "_fts"]
            )
        ),
    ]
