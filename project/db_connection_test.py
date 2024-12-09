# In your_project/your_app/management/commands/test_db_connection.py
from django.core.management.base import BaseCommand
import psycopg2

class Command(BaseCommand):
    help = 'Test database connection'

    def handle(self, *args, **options):
        try:
            conn = psycopg2.connect(
                dbname='backend',
                user='mysuperuser',
                password='mysuperuser',
                host='backend.czo628m24sbu.ap-southeast-2.rds.amazonaws.com',
                port='5432',
                connect_timeout=20
            )
            self.stdout.write(self.style.SUCCESS('✅ Connection Successful!'))
            conn.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection Failed: {e}'))