# Generated manually to fix file_id field length
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('woogawooga', '0002_modelregistry_processdfile_alter_systemlog_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inferenceresult',
            name='file_id',
            field=models.CharField(max_length=50, verbose_name='파일ID'),
        ),
    ]