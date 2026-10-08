import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0003_remove_parameter_alertable"),
    ]

    operations = [
        migrations.CreateModel(
            name="Forecast",
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
                ("target", models.CharField(max_length=32)),
                ("origin", models.DateTimeField()),
                ("ts", models.DateTimeField()),
                ("horizon_hour", models.PositiveSmallIntegerField()),
                ("prediction", models.FloatField()),
                ("lower_80", models.FloatField()),
                ("upper_80", models.FloatField()),
                ("lower_95", models.FloatField()),
                ("upper_95", models.FloatField()),
                ("model_name", models.CharField(max_length=64)),
                ("unit", models.CharField(blank=True, max_length=24)),
                ("source_data_cutoff", models.DateTimeField()),
                ("recent_coverage", models.FloatField(blank=True, null=True)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forecasts",
                        to="monitoring.node",
                    ),
                ),
            ],
            options={
                "ordering": ["node", "target", "ts"],
            },
        ),
        migrations.AddIndex(
            model_name="forecast",
            index=models.Index(
                fields=["node", "target", "ts"], name="idx_forecast_node_target_ts"
            ),
        ),
        migrations.AddConstraint(
            model_name="forecast",
            constraint=models.UniqueConstraint(
                fields=("node", "target", "origin", "ts"), name="uniq_forecast_row"
            ),
        ),
    ]
