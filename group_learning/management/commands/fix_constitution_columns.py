from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix missing columns in ConstitutionOption table for production'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing missing ConstitutionOption columns...")
        
        table_name = 'group_learning_constitutionoption'
        columns_to_add = [
            ('governance_impact', 'TEXT DEFAULT \'\''),
            ('country_state_changes', 'TEXT DEFAULT \'\''),
            ('score_reasoning', 'TEXT DEFAULT \'\''),
            ('societal_impact', 'TEXT DEFAULT \'\''),
        ]
        
        try:
            with transaction.atomic():
                for column_name, column_def in columns_to_add:
                    if not self._column_exists(table_name, column_name):
                        self.stdout.write(f"➕ Adding missing column: {column_name}")
                        self._add_column(table_name, column_name, column_def)
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Column {column_name} added successfully")
                        )
                    else:
                        self.stdout.write(f"✅ Column {column_name} already exists")
            
            self.stdout.write(
                self.style.SUCCESS("🎉 All columns verified/added successfully!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error during column fix: {e}")
            )
            raise

    def _column_exists(self, table_name, column_name):
        """Check if a column exists in the table."""
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                """, [table_name, column_name])
                return cursor.fetchone() is not None
            else:
                # SQLite
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                return any(col[1] == column_name for col in columns)

    def _add_column(self, table_name, column_name, column_def):
        """Add a column to the table."""
        with connection.cursor() as cursor:
            sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}'
            cursor.execute(sql)