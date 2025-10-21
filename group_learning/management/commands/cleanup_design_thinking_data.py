from django.core.management.base import BaseCommand
from django.db import transaction
from group_learning.models import (
    DesignThinkingSession, DesignTeam, TeamProgress, 
    TeamSubmission, DesignThinkingGame, DesignMission
)


class Command(BaseCommand):
    help = 'Clean up all Design Thinking game data for fresh start'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL Design Thinking game data. '
                    'Run with --confirm to proceed.'
                )
            )
            return

        self.stdout.write(self.style.HTTP_INFO('Starting cleanup of Design Thinking data...'))
        
        with transaction.atomic():
            # Count existing data before deletion
            sessions_count = DesignThinkingSession.objects.count()
            teams_count = DesignTeam.objects.count()
            progress_count = TeamProgress.objects.count()
            submissions_count = TeamSubmission.objects.count()
            
            self.stdout.write(f"Found:")
            self.stdout.write(f"  - {sessions_count} sessions")
            self.stdout.write(f"  - {teams_count} teams")
            self.stdout.write(f"  - {progress_count} progress records")
            self.stdout.write(f"  - {submissions_count} submissions")
            
            # Delete in proper order (respecting foreign key constraints)
            TeamSubmission.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Deleted all team submissions"))
            
            TeamProgress.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Deleted all team progress records"))
            
            DesignTeam.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Deleted all design teams"))
            
            DesignThinkingSession.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Deleted all design thinking sessions"))
            
            # Keep DesignThinkingGame and DesignMission for game structure
            self.stdout.write(self.style.HTTP_INFO("✓ Preserved game structure (games and missions)"))
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nCleanup completed! Design Thinking platform is ready for fresh sessions.'
            )
        )