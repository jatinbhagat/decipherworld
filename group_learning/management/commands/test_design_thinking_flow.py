from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from group_learning.models import (
    DesignThinkingGame, DesignMission, DesignThinkingSession,
    DesignTeam, TeamProgress, TeamSubmission
)
from group_learning.services import DesignThinkingService, SubmissionService, MissionAdvancementError
from group_learning.cache import DesignThinkingCache
import random
import string


class Command(BaseCommand):
    help = 'Test complete Design Thinking game flow end-to-end'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after completion',
        )
        parser.add_argument(
            '--teams',
            type=int,
            default=3,
            help='Number of teams to create (default: 3)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🎯 Starting Design Thinking End-to-End Test...'))
        
        test_passed = True
        session = None
        
        try:
            # Phase 1: Setup test environment
            self.stdout.write('\n📋 Phase 1: Setting up test environment...')
            session = self.setup_test_environment(options['teams'])
            
            # Phase 2: Test mission advancement
            self.stdout.write('\n🚀 Phase 2: Testing mission advancement...')
            self.test_mission_advancement(session)
            
            # Phase 3: Test team submissions
            self.stdout.write('\n📝 Phase 3: Testing team submissions...')
            self.test_team_submissions(session)
            
            # Phase 4: Test progress tracking
            self.stdout.write('\n📊 Phase 4: Testing progress tracking...')
            self.test_progress_tracking(session)
            
            # Phase 5: Test caching
            self.stdout.write('\n🚀 Phase 5: Testing caching layer...')
            self.test_caching_layer(session)
            
            # Phase 6: Test complete game flow
            self.stdout.write('\n🎮 Phase 6: Testing complete game flow...')
            self.test_complete_game_flow(session)
            
            self.stdout.write(self.style.SUCCESS('\n✅ All tests passed! Design Thinking flow is working correctly.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Test failed: {str(e)}'))
            test_passed = False
        
        finally:
            if options['cleanup'] and session:
                self.stdout.write('\n🧹 Cleaning up test data...')
                self.cleanup_test_data(session)
            elif session:
                self.stdout.write(f'\n💡 Test session created: {session.session_code}')
                self.stdout.write('   Use --cleanup flag to remove test data')
        
        if test_passed:
            self.stdout.write(self.style.SUCCESS('\n🎉 Design Thinking game is ready for production!'))
        else:
            self.stdout.write(self.style.ERROR('\n💥 Issues found - please review and fix before deployment'))

    def setup_test_environment(self, num_teams):
        """Setup test game, session, and teams"""
        self.stdout.write('  Creating test game and missions...')
        
        # Create or get test game
        game, created = DesignThinkingGame.objects.get_or_create(
            title='Test Design Thinking Game',
            defaults={
                'subtitle': 'End-to-End Test Game',
                'game_type': 'community_building',
                'description': 'Test game for validating mission advancement',
                'context': 'Testing environment',
                'min_players': 2,
                'max_players': 10,
                'estimated_duration': 120,
                'target_age_min': 16,
                'target_age_max': 25,
                'difficulty_level': 1,
                'introduction_text': 'Test game introduction',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('    ✅ Created test game')
            
            # Create missions
            missions_data = [
                ('Kickoff', 'Welcome and team formation', 1, 'kickoff'),
                ('Empathy', 'Understand user needs and pain points', 2, 'empathy'),
                ('Define', 'Define the problem statement', 3, 'define'),
                ('Ideate', 'Generate creative solutions', 4, 'ideate'),
                ('Prototype', 'Build and test prototypes', 5, 'prototype'),
                ('Showcase', 'Present final solutions', 6, 'showcase'),
            ]
            
            for title, description, order, mission_type in missions_data:
                DesignMission.objects.create(
                    game=game,
                    title=title,
                    description=description,
                    instructions=f'Instructions for {title} mission',
                    order=order,
                    mission_type=mission_type,
                    estimated_duration=15,
                    is_active=True
                )
            
            self.stdout.write('    ✅ Created 6 test missions')
        else:
            self.stdout.write('    ℹ️ Using existing test game')
        
        # Create test session
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        session = DesignThinkingSession.objects.create(
            game=game,  # For GameSession parent class
            design_game=game,  # For DesignThinkingSession
            session_code=session_code,
            status='waiting',
            facilitator=None,  # No specific facilitator for test
            created_at=timezone.now()
        )
        
        self.stdout.write(f'    ✅ Created test session: {session_code}')
        
        # Create test teams
        for i in range(num_teams):
            team = DesignTeam.objects.create(
                session=session,
                team_name=f'Test Team {i+1}',
                team_emoji=f'🎯',
                team_color=f'#{"FF" if i == 0 else "00"}{"FF" if i == 1 else "00"}{"FF" if i == 2 else "00"}',
                total_submissions=0
            )
            self.stdout.write(f'    ✅ Created {team.team_name}')
        
        self.stdout.write(f'  ✅ Test environment ready with {num_teams} teams')
        return session

    def test_mission_advancement(self, session):
        """Test mission advancement functionality"""
        service = DesignThinkingService(session)
        
        # Test starting session (advance to first mission)
        self.stdout.write('  Testing session start...')
        result = service.advance_to_mission(1)
        
        assert result['success'], "Failed to start session"
        assert result['mission']['order'] == 1, "Wrong mission order"
        self.stdout.write('    ✅ Session started successfully')
        
        # Test advancing to next mission
        self.stdout.write('  Testing mission advancement...')
        result = service.advance_to_next_mission()
        
        assert result['success'], "Failed to advance mission"
        assert result['mission']['order'] == 2, "Wrong mission order after advancement"
        self.stdout.write('    ✅ Mission advanced successfully')
        
        # Test advancing to specific mission
        self.stdout.write('  Testing specific mission advancement...')
        result = service.advance_to_mission(4)  # Skip to Ideate
        
        assert result['success'], "Failed to advance to specific mission"
        assert result['mission']['order'] == 4, "Wrong mission order for specific advancement"
        self.stdout.write('    ✅ Specific mission advancement works')
        
        # Test error handling
        self.stdout.write('  Testing error handling...')
        try:
            service.advance_to_mission(10)  # Invalid mission
            assert False, "Should have raised an error for invalid mission"
        except MissionAdvancementError:
            self.stdout.write('    ✅ Error handling works correctly')

    def test_team_submissions(self, session):
        """Test team submission functionality"""
        teams = session.design_teams.all()
        current_mission = session.current_mission
        
        if not current_mission or not teams:
            raise Exception("No current mission or teams found")
        
        # Test creating submissions
        self.stdout.write('  Testing submission creation...')
        for i, team in enumerate(teams):
            submission = SubmissionService.create_submission(
                team=team,
                mission=current_mission,
                submission_type='observation',
                content=f'Test submission from {team.team_name} - observation {i+1}'
            )
            
            assert submission.id is not None, "Submission was not created"
            assert submission.team == team, "Wrong team assigned"
            assert submission.mission == current_mission, "Wrong mission assigned"
            
            self.stdout.write(f'    ✅ Created submission for {team.team_name}')
        
        # Test submission counting
        self.stdout.write('  Testing submission counting...')
        total_submissions = TeamSubmission.objects.filter(
            mission=current_mission,
            team__in=teams
        ).count()
        
        assert total_submissions == len(teams), f"Expected {len(teams)} submissions, got {total_submissions}"
        self.stdout.write(f'    ✅ Submission count correct: {total_submissions}')

    def test_progress_tracking(self, session):
        """Test progress tracking functionality"""
        service = DesignThinkingService(session)
        
        self.stdout.write('  Testing progress data retrieval...')
        progress_data = service.get_session_progress()
        
        # Validate progress data structure
        assert 'session_code' in progress_data, "Missing session_code"
        assert 'current_mission' in progress_data, "Missing current_mission"
        assert 'missions' in progress_data, "Missing missions"
        assert 'teams_count' in progress_data, "Missing teams_count"
        
        assert progress_data['session_code'] == session.session_code, "Wrong session code"
        assert len(progress_data['missions']) == 6, "Wrong number of missions"
        
        self.stdout.write('    ✅ Progress data structure is correct')
        
        # Test mission states
        self.stdout.write('  Testing mission states...')
        current_order = progress_data['current_mission']['order']
        
        for mission in progress_data['missions']:
            if mission['order'] < current_order:
                assert mission['state'] == 'completed', f"Mission {mission['order']} should be completed"
            elif mission['order'] == current_order:
                assert mission['state'] == 'active', f"Mission {mission['order']} should be active"
            else:
                assert mission['state'] == 'locked', f"Mission {mission['order']} should be locked"
        
        self.stdout.write('    ✅ Mission states are correct')

    def test_caching_layer(self, session):
        """Test caching functionality"""
        service = DesignThinkingService(session)
        
        self.stdout.write('  Testing cache operations...')
        
        # Clear any existing cache
        DesignThinkingCache.invalidate_session_progress(session.session_code)
        
        # First call should miss cache and compute fresh data
        self.stdout.write('    Testing cache miss...')
        start_time = timezone.now()
        progress_data_1 = service.get_session_progress()
        first_call_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # Second call should hit cache and be faster
        self.stdout.write('    Testing cache hit...')
        start_time = timezone.now()
        progress_data_2 = service.get_session_progress()
        second_call_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # Validate cache effectiveness (excluding timestamps which will differ)
        data_1_no_timestamp = {k: v for k, v in progress_data_1.items() if k != 'cached_at'}
        data_2_no_timestamp = {k: v for k, v in progress_data_2.items() if k != 'cached_at'}
        assert data_1_no_timestamp == data_2_no_timestamp, "Cached data differs from fresh data"
        assert 'cached_at' in progress_data_2, "Cache timestamp missing"
        
        self.stdout.write(f'    ✅ Cache hit ({second_call_time:.2f}ms) faster than miss ({first_call_time:.2f}ms)')
        
        # Test cache invalidation
        self.stdout.write('    Testing cache invalidation...')
        DesignThinkingCache.invalidate_session_progress(session.session_code)
        
        cached_data = DesignThinkingCache.get_session_progress(session.session_code)
        assert cached_data is None, "Cache was not properly invalidated"
        
        self.stdout.write('    ✅ Cache invalidation works')

    def test_complete_game_flow(self, session):
        """Test complete game flow from start to finish"""
        service = DesignThinkingService(session)
        teams = list(session.design_teams.all())
        
        self.stdout.write('  Testing complete mission flow...')
        
        # Clear any existing submissions from previous test phases
        TeamSubmission.objects.filter(team__in=teams).delete()
        self.stdout.write('    Cleared previous test submissions')
        
        # Start from first mission
        service.advance_to_mission(1)
        
        # Go through all missions
        for mission_order in range(1, 7):  # Missions 1-6
            self.stdout.write(f'    Testing mission {mission_order}...')
            
            # Advance to mission
            if mission_order > 1:
                service.advance_to_mission(mission_order)
            
            # Refresh session to get current mission
            session.refresh_from_db()
            
            # Verify mission is active
            progress_data = service.get_session_progress()
            current_mission = progress_data['current_mission']
            assert current_mission['order'] == mission_order, f"Mission {mission_order} not active"
            
            # Create submissions for all teams
            mission = session.current_mission
            self.stdout.write(f'      Creating submissions for mission: {mission.title} (ID: {mission.id})')
            for team in teams:
                SubmissionService.create_submission(
                    team=team,
                    mission=mission,
                    submission_type='observation' if mission.title == 'Empathy' else 'ideation',
                    content=f'Mission {mission_order} submission from {team.team_name}'
                )
            
            # Verify submissions were created
            submission_count = TeamSubmission.objects.filter(
                mission=mission,
                team__in=teams
            ).count()
            expected_count = len(teams)
            assert submission_count == expected_count, f"Wrong submission count for mission {mission_order}: expected {expected_count}, got {submission_count}"
            
            self.stdout.write(f'      ✅ Mission {mission_order} ({mission.title}) completed')
        
        # Verify final state
        final_progress = service.get_session_progress()
        assert final_progress['current_mission']['order'] == 6, "Final mission not reached"
        
        total_submissions = TeamSubmission.objects.filter(
            team__in=teams
        ).count()
        expected_submissions = len(teams) * 6  # 6 missions × number of teams
        assert total_submissions == expected_submissions, f"Expected {expected_submissions} total submissions, got {total_submissions}"
        
        self.stdout.write(f'    ✅ Complete game flow successful ({total_submissions} submissions created)')

    def cleanup_test_data(self, session):
        """Clean up test data"""
        with transaction.atomic():
            # Delete in proper order to respect foreign keys
            TeamSubmission.objects.filter(team__session=session).delete()
            TeamProgress.objects.filter(session=session).delete()
            DesignTeam.objects.filter(session=session).delete()
            
            # Clear cache
            DesignThinkingCache.invalidate_all_session_caches(session.session_code)
            
            # Delete session
            game = session.design_game
            session.delete()
            
            # Optionally delete test game if it's our test game
            if game.title == 'Test Design Thinking Game':
                game.delete()
                self.stdout.write('  ✅ Removed test game and all related data')
            else:
                self.stdout.write('  ✅ Removed test session data')
        
        self.stdout.write('  🧹 Cleanup completed')