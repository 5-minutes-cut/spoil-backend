# Generated manual initial migration for series app
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='series_photos/')),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
            },
        ),
    ]
