from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='max_capacity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='min_capacity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='requires_approval',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='is_free',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
