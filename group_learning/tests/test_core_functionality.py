"""
Core functionality tests for simplified Design Thinking system
Tests essential features without complex setup
"""

import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from group_learning.models import (
    DesignThinkingGame, DesignMission, DesignThinkingSession,
    DesignTeam, SimplifiedPhaseInput, PhaseCompletionTracker
)
from group_learning.auto_progression_service import AutoProgressionService

User = get_user_model()


class CoreFunctionalityTests(TestCase):
    """Test core functionality of simplified Design Thinking system"""
    
    def setUp(self):
        """Set up minimal test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create minimal game setup
        self.game = DesignThinkingGame.objects.create(
            title='Test Game',
            subtitle='Test Subtitle',
            game_type='social_issue',
            description='Test game description',
            context='Test context',
            min_players=2,
            max_players=8,
            estimated_duration=45,
            difficulty_level=2,  # 2 = Intermediate
            target_age_min=14,
            target_age_max=18,
            auto_advance_enabled=True,
            completion_threshold_percentage=100,
            phase_transition_delay=3,
            max_teams_per_session=10,
            session_timeout_minutes=120
        )
        
        self.mission = DesignMission.objects.create(
            game=self.game,
            mission_type='empathy',
            title='Test Mission',
            description='Test mission description',
            order=1,
            is_active=True
        )
        
        self.session = DesignThinkingSession.objects.create(
            game=self.game,  # Required by parent GameSession
            design_game=self.game,
            session_code='TEST123',
            current_mission=self.mission
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Test Team',
            team_emoji='🚀',
            team_members=[{'name': 'Student1', 'session_id': 'student_1'}]
        )
    
    def test_auto_progression_service_basic(self):
        """Test basic auto-progression service functionality"""
        service = AutoProgressionService()
        
        # Test successful input processing
        result = service.process_phase_input(
            team_id=self.team.id,
            mission_id=self.mission.id,
            student_data={'name': 'Test Student', 'session_id': 'test_123'},
            input_data=[{
                'type': 'radio',
                'label': 'Test Question',
                'value': 'Test Answer',
                'order': 1
            }]
        )
        
        self.assertTrue(result['success'])
        self.assertIn('completion_result', result)
        self.assertIn('progression_result', result)
        
        # Verify input was saved
        saved_input = SimplifiedPhaseInput.objects.filter(
            team=self.team,
            mission=self.mission,
            student_session_id='test_123'
        ).first()
        
        self.assertIsNotNone(saved_input)
        self.assertEqual(saved_input.input_type, 'radio')
        self.assertEqual(saved_input.selected_value, 'Test Answer')
    
    def test_simplified_phase_input_model(self):
        """Test SimplifiedPhaseInput model creation and validation"""
        input_data = SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=self.mission,
            session=self.session,
            student_name='Test Student',
            student_session_id='test_student_123',
            input_type='radio',
            input_label='What is your favorite color?',
            selected_value='Blue',
            input_order=1,
            time_to_complete_seconds=30
        )
        
        self.assertEqual(input_data.team, self.team)
        self.assertEqual(input_data.mission, self.mission)
        self.assertEqual(input_data.input_type, 'radio')
        self.assertTrue(input_data.is_active)
        self.assertIsNotNone(input_data.submitted_at)
    
    def test_phase_completion_tracker(self):
        """Test phase completion tracking functionality"""
        tracker = PhaseCompletionTracker.objects.create(
            session=self.session,
            team=self.team,
            mission=self.mission,
            total_required_inputs=3,
            completed_inputs=0
        )
        
        # Test updating completion status
        tracker.completed_inputs = 1
        is_ready = tracker.update_completion_status()
        self.assertFalse(is_ready)  # 1/3 not complete
        
        tracker.completed_inputs = 3
        is_ready = tracker.update_completion_status()
        self.assertTrue(is_ready)  # 3/3 complete
        self.assertEqual(tracker.completion_percentage, 100.0)
    
    def test_input_validation_basic(self):
        """Test basic input validation"""
        service = AutoProgressionService()
        
        # Test missing required fields
        result = service.process_phase_input(
            team_id=None,
            mission_id=self.mission.id,
            student_data={'name': 'Test', 'session_id': 'test'},
            input_data=[]
        )
        self.assertFalse(result['success'])
        self.assertIn('Missing required parameters', result['error'])
        
        # Test invalid input type
        result = service.process_phase_input(
            team_id=self.team.id,
            mission_id=self.mission.id,
            student_data={'name': 'Test', 'session_id': 'test'},
            input_data=[{
                'type': 'invalid_type',
                'label': 'Test',
                'value': 'Test',
                'order': 1
            }]
        )
        self.assertFalse(result['success'])
        self.assertIn('Invalid input type', result['error'])
    
    def test_teacher_scoring(self):
        """Test teacher scoring functionality"""
        # First create an input
        SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=self.mission,
            session=self.session,
            student_name='Test Student',
            student_session_id='test_student_123',
            input_type='radio',
            input_label='Test Question',
            selected_value='Test Answer',
            input_order=1
        )
        
        service = AutoProgressionService()
        
        # Test scoring
        success = service.save_teacher_score(
            team_id=self.team.id,
            mission_id=self.mission.id,
            score='A',
            teacher_id='teacher_123'
        )
        
        self.assertTrue(success)
        
        # Verify score was saved
        scored_input = SimplifiedPhaseInput.objects.filter(
            team=self.team,
            mission=self.mission,
            teacher_score='A'
        ).first()
        
        self.assertIsNotNone(scored_input)
        self.assertEqual(scored_input.teacher_score, 'A')
        self.assertIsNotNone(scored_input.scored_at)
    
    def test_session_creation_basic(self):
        """Test basic session creation functionality"""
        new_session = DesignThinkingSession.objects.create(
            game=self.game,
            design_game=self.game,
            session_code='NEW123',
            current_mission=self.mission
        )
        
        self.assertEqual(new_session.design_game, self.game)
        self.assertEqual(new_session.session_code, 'NEW123')
        self.assertIsNotNone(new_session.design_game)  # Verify session is properly configured
        self.assertIsNotNone(new_session.created_at)


class MonitoringBasicTests(TestCase):
    """Test basic monitoring functionality"""
    
    def test_performance_monitor_import(self):
        """Test that monitoring modules can be imported"""
        from group_learning.monitoring import (
            performance_monitor, activity_monitor, connection_monitor
        )
        
        self.assertIsNotNone(performance_monitor)
        self.assertIsNotNone(activity_monitor)
        self.assertIsNotNone(connection_monitor)
    
    def test_logging_functions_import(self):
        """Test that logging functions can be imported"""
        from group_learning.monitoring import (
            log_operation, log_session_activity, log_error, log_websocket_event
        )
        
        # These should be callable
        self.assertTrue(callable(log_operation))
        self.assertTrue(callable(log_session_activity))
        self.assertTrue(callable(log_error))
        self.assertTrue(callable(log_websocket_event))


if __name__ == '__main__':
    import unittest
    unittest.main()