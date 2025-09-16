from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import logging


class Command(BaseCommand):
    help = 'Check and fix robotic buddy database tables'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        self.stdout.write(f"Database backend: {settings.DATABASES['default']['ENGINE']}")
        
        # First, try to directly test the model
        try:
            from robotic_buddy.models import RoboticBuddy
            
            # Try a simple count query
            try:
                count = RoboticBuddy.objects.count()
                self.stdout.write(self.style.SUCCESS(f"✅ RoboticBuddy table exists. Current count: {count}"))
                
                # Test create operation
                import uuid
                test_session_id = f"test-{uuid.uuid4()}"
                test_buddy = RoboticBuddy.objects.create(
                    name="Test Buddy",
                    session_id=test_session_id,
                    personality="cheerful",
                    primary_color="blue",
                    secondary_color="green"
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Created test buddy with ID: {test_buddy.id}"))
                
                # Clean up
                test_buddy.delete()
                self.stdout.write(self.style.SUCCESS("✅ Test buddy cleaned up successfully"))
                
            except Exception as model_error:
                self.stdout.write(self.style.ERROR(f"❌ RoboticBuddy model error: {str(model_error)}"))
                
                # The table likely doesn't exist, try to run migrations
                self.stdout.write(self.style.WARNING("🔧 Running robotic_buddy migrations..."))
                
                from django.core.management import call_command
                try:
                    call_command('migrate', 'robotic_buddy', verbosity=2)
                    self.stdout.write(self.style.SUCCESS("✅ Migrations completed successfully"))
                    
                    # Test again after migration
                    count = RoboticBuddy.objects.count()
                    self.stdout.write(self.style.SUCCESS(f"✅ After migration - RoboticBuddy count: {count}"))
                    
                except Exception as migrate_error:
                    self.stdout.write(self.style.ERROR(f"❌ Migration failed: {str(migrate_error)}"))
                    logger.error(f"Migration failed: {str(migrate_error)}", exc_info=True)
                    
        except ImportError as import_error:
            self.stdout.write(self.style.ERROR(f"❌ Cannot import RoboticBuddy model: {str(import_error)}"))
            logger.error(f"Import error: {str(import_error)}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {str(e)}"))
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            
        # Show migration status
        try:
            from django.core.management import call_command
            self.stdout.write("\n📋 Current migration status:")
            call_command('showmigrations', 'robotic_buddy')
        except Exception as e:
            self.stdout.write(f"❌ Could not show migrations: {str(e)}")