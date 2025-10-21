from django.core.management.base import BaseCommand
from django.db import transaction
from group_learning.models import DesignThinkingSession, TeamProgress, DesignMission, TeamSubmission


class Command(BaseCommand):
    help = 'Check and fix Design Thinking game data consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix inconsistencies found',
        )
        parser.add_argument(
            '--session-code',
            type=str,
            help='Check specific session only',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('Starting Design Thinking consistency check...'))
        
        sessions = DesignThinkingSession.objects.select_related('design_game').all()
        if options['session_code']:
            sessions = sessions.filter(session_code=options['session_code'])
        
        total_issues = 0
        fixed_issues = 0

        for session in sessions:
            self.stdout.write(f"\nChecking session: {session.session_code}")
            
            # Check 1: Teams without proper TeamProgress records
            teams = session.design_teams.all()
            missions = session.design_game.missions.filter(is_active=True).order_by('order')
            
            for team in teams:
                # Check if team has progress records for all missions up to current
                current_mission_order = 0
                if session.current_mission:
                    current_mission_order = session.current_mission.order
                
                expected_missions = missions.filter(order__lte=current_mission_order)
                existing_progress = TeamProgress.objects.filter(
                    session=session, team=team, mission__in=expected_missions
                )
                
                missing_count = expected_missions.count() - existing_progress.count()
                if missing_count > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Team {team.team_name}: Missing {missing_count} TeamProgress records"
                        )
                    )
                    total_issues += missing_count
                    
                    if options['fix']:
                        with transaction.atomic():
                            for mission in expected_missions:
                                progress, created = TeamProgress.objects.get_or_create(
                                    session=session, team=team, mission=mission
                                )
                                if created:
                                    fixed_issues += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"    Created TeamProgress for {team.team_name} - {mission.title}"
                                        )
                                    )
            
            # Check 2: Orphaned TeamProgress records (missions beyond current)
            if session.current_mission:
                future_missions = missions.filter(order__gt=session.current_mission.order)
                orphaned_progress = TeamProgress.objects.filter(
                    session=session, mission__in=future_missions
                )
                
                if orphaned_progress.exists():
                    orphaned_count = orphaned_progress.count()
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Found {orphaned_count} orphaned TeamProgress records for future missions"
                        )
                    )
                    total_issues += orphaned_count
                    
                    if options['fix']:
                        deleted_count = orphaned_progress.delete()[0]
                        fixed_issues += deleted_count
                        self.stdout.write(
                            self.style.SUCCESS(f"    Deleted {deleted_count} orphaned records")
                        )
            
            # Check 3: TeamProgress completion status consistency
            for team in teams:
                team_progress_records = TeamProgress.objects.filter(session=session, team=team)
                for progress in team_progress_records:
                    # Check if completion status matches submission count for Empathy mission
                    if progress.mission.title == "Empathy":
                        submission_count = TeamSubmission.objects.filter(
                            team=team, 
                            mission=progress.mission,
                            submission_type='observation'
                        ).count()
                        expected_complete = submission_count >= 5  # Based on empathy mission requirement
                        
                        if progress.is_completed != expected_complete:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Team {team.team_name} Empathy mission: completion status mismatch "
                                    f"(is_completed={progress.is_completed}, submissions={submission_count})"
                                )
                            )
                            total_issues += 1
                            
                            if options['fix']:
                                progress.is_completed = expected_complete
                                progress.save()
                                fixed_issues += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"    Fixed completion status for {team.team_name} Empathy mission"
                                    )
                                )

        # Summary
        self.stdout.write(f"\n{self.style.HTTP_INFO('Consistency Check Summary:')}")
        self.stdout.write(f"Total issues found: {total_issues}")
        if options['fix']:
            self.stdout.write(f"Issues fixed: {fixed_issues}")
            self.stdout.write(self.style.SUCCESS("Database consistency check completed with fixes applied."))
        else:
            self.stdout.write("Run with --fix to automatically resolve issues.")
            self.stdout.write(self.style.HTTP_INFO("Database consistency check completed (read-only mode)."))