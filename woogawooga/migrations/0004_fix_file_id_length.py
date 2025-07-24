# Generated manually to fix file_id field length with SQL
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('woogawooga', '0003_alter_inferenceresult_file_id'),
    ]

    operations = [
        # SQL을 직접 실행하여 컬럼 길이 변경
        migrations.RunSQL(
            sql="ALTER TABLE InferenceResult MODIFY file_id VARCHAR(50);",
            reverse_sql="ALTER TABLE InferenceResult MODIFY file_id VARCHAR(20);"
        ),
    ]