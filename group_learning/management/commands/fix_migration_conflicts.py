from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Fix migration conflicts by marking migrations as applied if tables exist'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting migration conflict fix...'))
        
        # List of migrations that might have conflicts
        problematic_migrations = [
            ('group_learning', '0009_add_climate_game_models'),
            ('group_learning', '0010_alter_climateplayerresponse_climate_scenario_and_more'),
            ('group_learning', '0011_climategamesession_current_timer_end_and_more'),
            ('group_learning', '0012_alter_climategamesession_round_duration_minutes'),
        ]
        
        with connection.cursor() as cursor:
            # Check if climate game table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'group_learning_climategame'
            """)
            climate_table_exists = cursor.fetchone() is not None
            
            self.stdout.write(f'ClimateGame table exists: {climate_table_exists}')
            
            if climate_table_exists:
                # Mark migrations as applied if table exists
                recorder = MigrationRecorder(connection)
                
                for app_label, migration_name in problematic_migrations:
                    # Check if migration is recorded
                    if not recorder.migration_qs.filter(
                        app=app_label, 
                        name=migration_name
                    ).exists():
                        recorder.record_applied(app_label, migration_name)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Marked {app_label}.{migration_name} as applied'
                            )
                        )
                    else:
                        self.stdout.write(
                            f'{app_label}.{migration_name} already recorded as applied'
                        )
            
            # Run a safe migrate to catch up any remaining migrations
            try:
                from django.core.management import call_command
                call_command('migrate', 'group_learning', verbosity=0)
                self.stdout.write(self.style.SUCCESS('Migration sync completed successfully'))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Migration sync had issues: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('Migration conflict fix completed'))