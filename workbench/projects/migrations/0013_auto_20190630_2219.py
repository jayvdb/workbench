# Generated by Django 2.2.2 on 2019-06-30 20:19

from django.db import migrations


def forwards(apps, schema_editor):
    Model = apps.get_model("projects.Project")
    for instance in Model.objects.select_related("customer", "contact"):
        instance._fts = " ".join(
            str(part)
            for part in [
                "%s-%04d" % (instance.created_at.year, instance._code),
                instance.customer.name,
                instance.contact.given_name if instance.contact else "",
                instance.contact.family_name if instance.contact else "",
            ]
        )
        instance.save()


class Migration(migrations.Migration):

    dependencies = [("projects", "0012_project__fts")]

    operations = [migrations.RunPython(forwards)]
