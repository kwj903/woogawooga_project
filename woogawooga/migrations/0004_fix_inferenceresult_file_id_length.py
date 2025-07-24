# Manual migration to fix file_id field length issue
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('woogawooga', '0003_alter_inferenceresult_file_id'),
    ]

    operations = [
        # SQL 직접 실행으로 확실하게 컬럼 길이 변경
        migrations.RunSQL(
            "ALTER TABLE InferenceResult MODIFY file_id VARCHAR(50);",
            reverse_sql="ALTER TABLE InferenceResult MODIFY file_id VARCHAR(20);"
        ),
        
        # 모델 필드도 다시 한번 명시적으로 변경
        migrations.AlterField(
            model_name='inferenceresult',
            name='file_id',
            field=models.CharField(max_length=50, verbose_name='파일ID'),
        ),
    ]