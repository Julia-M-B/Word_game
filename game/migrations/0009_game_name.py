# Generated by Django 5.1.6 on 2025-03-02 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0008_rename_start_category_game_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
