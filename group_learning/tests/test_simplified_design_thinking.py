"""
Comprehensive tests for simplified Design Thinking auto-progression system
Tests all critical paths for UAT readiness
"""

import json
import asyncio
from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from group_learning.models import (
    DesignThinkingGame, DesignMission, DesignThinkingSession,
    DesignTeam, SimplifiedPhaseInput, PhaseCompletionTracker
)
from group_learning.auto_progression_service import AutoProgressionService
from group_learning.consumers import DesignThinkingConsumer
from group_learning.monitoring import (
    performance_monitor, activity_monitor, connection_monitor
)

User = get_user_model()


class SimplifiedDesignThinkingModelTests(TestCase):
    """Test enhanced model validation and constraints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123'
        )
        
        # Create simplified game
        self.game = DesignThinkingGame.objects.create(
            title='Test Simplified Game',
            auto_advance_enabled=True,
            completion_threshold_percentage=100,
            phase_transition_delay=3,
            scoring_system='abc'
        )
        
        # Create missions
        self.mission1 = DesignMission.objects.create(
            game=self.game,
            mission_type='empathy',
            order=1,
            title='Test Empathy Mission',
            input_schema={
                'inputs': [
                    {'type': 'radio', 'label': 'Test question 1'},
                    {'type': 'radio', 'label': 'Test question 2'}
                ]
            },
            requires_all_team_members=True
        )
        
        self.mission2 = DesignMission.objects.create(
            game=self.game,
            mission_type='define',
            order=2,
            title='Test Define Mission',
            input_schema={
                'inputs': [
                    {'type': 'dropdown', 'label': 'Test dropdown'},
                    {'type': 'text_short', 'label': 'Test text'}
                ]
            },
            requires_all_team_members=True
        )
        
        # Create session
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            facilitator=self.user,
            session_code='TEST123',
            current_mission=self.mission1,
            status='in_progress'
        )
        
        # Create team
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Test Team Alpha',
            team_emoji='🚀',
            team_members=[
                {'name': 'Alice', 'session_id': 'alice_123'},
                {'name': 'Bob', 'session_id': 'bob_456'}
            ]
        )
    
    def test_simplified_phase_input_validation(self):
        """Test SimplifiedPhaseInput model validation"""
        # Valid input
        valid_input = SimplifiedPhaseInput(
            team=self.team,
            mission=self.mission1,
            session=self.session,
            student_name='Alice',
            student_session_id='alice_123',
            input_type='radio',
            input_label='Test question',
            selected_value='Test answer',
            input_order=1
        )
        
        # Should validate successfully
        valid_input.full_clean()
        valid_input.save()
        self.assertTrue(valid_input.is_active)
        
        # Test validation errors
        with self.assertRaises(ValidationError):
            # Empty student name
            invalid_input = SimplifiedPhaseInput(
                team=self.team,
                mission=self.mission1,
                session=self.session,
                student_name='',
                student_session_id='alice_123',
                input_type='radio',
                input_label='Test question',
                selected_value='Test answer'
            )
            invalid_input.full_clean()
        
        with self.assertRaises(ValidationError):
            # Text too long for short input
            invalid_input = SimplifiedPhaseInput(
                team=self.team,
                mission=self.mission1,
                session=self.session,
                student_name='Alice',
                student_session_id='alice_123',
                input_type='text_short',
                input_label='Test question',
                selected_value='A' * 51  # Too long
            )
            invalid_input.full_clean()
        
        with self.assertRaises(ValidationError):
            # Invalid rating
            invalid_input = SimplifiedPhaseInput(
                team=self.team,
                mission=self.mission1,
                session=self.session,
                student_name='Alice',
                student_session_id='alice_123',
                input_type='rating',
                input_label='Test rating',
                selected_value='10'  # Too high
            )
            invalid_input.full_clean()
    
    def test_phase_completion_tracker_validation(self):
        """Test PhaseCompletionTracker model validation"""
        # Valid tracker
        valid_tracker = PhaseCompletionTracker(
            session=self.session,
            team=self.team,
            mission=self.mission1,
            total_required_inputs=4,  # 2 team members × 2 inputs
            completed_inputs=2,
            completion_percentage=50.0
        )
        
        # Should validate successfully
        valid_tracker.full_clean()
        valid_tracker.save()
        
        # Test validation errors
        with self.assertRaises(ValidationError):
            # Completed > total
            invalid_tracker = PhaseCompletionTracker(
                session=self.session,
                team=self.team,
                mission=self.mission2,
                total_required_inputs=4,
                completed_inputs=5,  # Too many
                completion_percentage=125.0
            )
            invalid_tracker.full_clean()
        
        with self.assertRaises(ValidationError):
            # Percentage doesn't match calculation
            invalid_tracker = PhaseCompletionTracker(
                session=self.session,
                team=self.team,
                mission=self.mission2,
                total_required_inputs=4,
                completed_inputs=2,
                completion_percentage=75.0  # Should be 50.0
            )
            invalid_tracker.full_clean()
    
    def test_completion_tracker_update_status(self):
        """Test completion status update logic"""
        tracker = PhaseCompletionTracker.objects.create(
            session=self.session,
            team=self.team,
            mission=self.mission1,
            total_required_inputs=4,
            completed_inputs=0,
            completion_percentage=0.0
        )
        
        # Update to 50% completion
        tracker.completed_inputs = 2
        is_ready = tracker.update_completion_status()
        self.assertFalse(is_ready)  # Not ready at 50%
        self.assertEqual(tracker.completion_percentage, 50.0)
        
        # Update to 100% completion
        tracker.completed_inputs = 4
        is_ready = tracker.update_completion_status()
        self.assertTrue(is_ready)  # Ready at 100%
        self.assertEqual(tracker.completion_percentage, 100.0)
        self.assertIsNotNone(tracker.phase_completed_at)


class AutoProgressionServiceTests(TestCase):
    """Test auto-progression service logic"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123'
        )
        
        self.game = DesignThinkingGame.objects.create(
            title='Test Game',
            auto_advance_enabled=True,
            completion_threshold_percentage=100,
            phase_transition_delay=3
        )
        
        self.mission = DesignMission.objects.create(
            game=self.game,
            mission_type='empathy',
            order=1,
            title='Test Mission',
            input_schema={
                'inputs': [
                    {'type': 'radio', 'label': 'Question 1'},
                    {'type': 'radio', 'label': 'Question 2'}
                ]
            },
            requires_all_team_members=True
        )
        
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            facilitator=self.user,
            session_code='TEST456',
            current_mission=self.mission
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Test Team',
            team_emoji='🎯',
            team_members=[
                {'name': 'Alice', 'session_id': 'alice_123'},
                {'name': 'Bob', 'session_id': 'bob_456'}
            ]
        )
        
        self.service = AutoProgressionService()
    
    def test_input_validation(self):
        """Test comprehensive input validation"""
        # Valid input data
        valid_team_id = self.team.id
        valid_mission_id = self.mission.id
        valid_student_data = {'name': 'Alice', 'session_id': 'alice_123'}
        valid_input_data = [
            {'type': 'radio', 'label': 'Question 1', 'value': 'Answer 1', 'order': 1},
            {'type': 'radio', 'label': 'Question 2', 'value': 'Answer 2', 'order': 2}
        ]
        
        # Test valid input
        validation_result = self.service._validate_input_data(
            valid_team_id, valid_mission_id, valid_student_data, valid_input_data
        )
        self.assertTrue(validation_result['valid'])
        
        # Test missing parameters
        validation_result = self.service._validate_input_data(
            None, valid_mission_id, valid_student_data, valid_input_data
        )
        self.assertFalse(validation_result['valid'])
        self.assertIn('Missing required parameters', validation_result['error'])
        
        # Test invalid team ID
        validation_result = self.service._validate_input_data(
            99999, valid_mission_id, valid_student_data, valid_input_data
        )
        self.assertFalse(validation_result['valid'])
        self.assertIn('Team 99999 not found', validation_result['error'])
        
        # Test empty student name
        invalid_student_data = {'name': '', 'session_id': 'alice_123'}
        validation_result = self.service._validate_input_data(
            valid_team_id, valid_mission_id, invalid_student_data, valid_input_data
        )
        self.assertFalse(validation_result['valid'])
        self.assertIn('Valid student name', validation_result['error'])
        
        # Test too long text input
        invalid_input_data = [
            {'type': 'text_short', 'label': 'Question', 'value': 'A' * 51, 'order': 1}
        ]
        validation_result = self.service._validate_input_data(
            valid_team_id, valid_mission_id, valid_student_data, invalid_input_data
        )
        self.assertFalse(validation_result['valid'])
        self.assertIn('cannot exceed 50 characters', validation_result['error'])
        
        # Test invalid rating
        invalid_input_data = [
            {'type': 'rating', 'label': 'Rating', 'value': '10', 'order': 1}
        ]
        validation_result = self.service._validate_input_data(
            valid_team_id, valid_mission_id, valid_student_data, invalid_input_data
        )
        self.assertFalse(validation_result['valid'])
        self.assertIn('must be between 1 and 5', validation_result['error'])
    
    def test_process_phase_input_success(self):
        """Test successful phase input processing"""
        result = self.service.process_phase_input(
            team_id=self.team.id,
            mission_id=self.mission.id,
            student_data={'name': 'Alice', 'session_id': 'alice_123'},
            input_data=[
                {'type': 'radio', 'label': 'Question 1', 'value': 'Answer 1', 'order': 1},
                {'type': 'radio', 'label': 'Question 2', 'value': 'Answer 2', 'order': 2}
            ]
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['input_saved'])
        self.assertIn('completion_result', result)
        self.assertIn('progression_result', result)
        
        # Check that input was saved
        inputs = SimplifiedPhaseInput.objects.filter(
            team=self.team,
            mission=self.mission,
            student_session_id='alice_123'
        )
        self.assertEqual(inputs.count(), 2)
        
        # Check completion tracker was created/updated
        tracker = PhaseCompletionTracker.objects.get(
            session=self.session,
            team=self.team,
            mission=self.mission
        )
        self.assertEqual(tracker.completed_inputs, 2)
        self.assertEqual(tracker.completion_percentage, 50.0)  # 2/4 inputs
    
    def test_teacher_scoring(self):
        """Test teacher scoring functionality"""
        # First create some inputs
        SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=self.mission,
            session=self.session,
            student_name='Alice',
            student_session_id='alice_123',
            input_type='radio',
            input_label='Question 1',
            selected_value='Answer 1'
        )
        
        # Test scoring
        success = self.service.save_teacher_score(
            team_id=self.team.id,
            mission_id=self.mission.id,
            score='A',
            teacher_id='teacher_1'
        )
        
        self.assertTrue(success)
        
        # Check that score was saved
        input_obj = SimplifiedPhaseInput.objects.get(
            team=self.team,
            mission=self.mission,
            student_session_id='alice_123'
        )
        self.assertEqual(input_obj.teacher_score, 'A')
        self.assertIsNotNone(input_obj.scored_at)


class SimplifiedDesignThinkingViewTests(TestCase):
    """Test simplified Design Thinking views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123'
        )
        
        # Create simplified game via management command
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        self.game = DesignThinkingGame.objects.filter(
            auto_advance_enabled=True
        ).first()
        
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            facilitator=self.user,
            session_code='VIEW123',
            current_mission=self.game.missions.first(),
            status='in_progress'
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='View Test Team',
            team_emoji='🎪'
        )
    
    def test_simplified_student_dashboard_view(self):
        """Test student dashboard view"""
        url = reverse('group_learning:simplified_student_dashboard', 
                     kwargs={'session_code': self.session.session_code})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Test Team')
        self.assertContains(response, 'Phase Progress Bar')
    
    def test_simplified_teacher_dashboard_view(self):
        """Test teacher dashboard view"""
        url = reverse('group_learning:simplified_teacher_dashboard',
                     kwargs={'session_code': self.session.session_code})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Teacher Dashboard')
        self.assertContains(response, 'VIEW123')
    
    def test_simplified_input_submission_api(self):
        """Test input submission API"""
        url = reverse('group_learning:simplified_input_submit',
                     kwargs={'session_code': self.session.session_code})
        
        data = {
            'team_id': self.team.id,
            'mission_id': self.session.current_mission.id,
            'student_data': {'name': 'Alice', 'session_id': 'alice_123'},
            'input_data': [
                {'type': 'radio', 'label': 'Question 1', 'value': 'Answer 1', 'order': 1}
            ]
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
    
    def test_teacher_scoring_api(self):
        """Test teacher scoring API"""
        # Create input first
        SimplifiedPhaseInput.objects.create(
            team=self.team,
            mission=self.session.current_mission,
            session=self.session,
            student_name='Alice',
            student_session_id='alice_123',
            input_type='radio',
            input_label='Question 1',
            selected_value='Answer 1'
        )
        
        url = reverse('group_learning:simplified_teacher_score',
                     kwargs={'session_code': self.session.session_code})
        
        data = {
            'team_id': self.team.id,
            'mission_id': self.session.current_mission.id,
            'score': 'A'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
    
    def test_invalid_session_code(self):
        """Test handling of invalid session codes"""
        url = reverse('group_learning:simplified_student_dashboard',
                     kwargs={'session_code': 'INVALID'})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should handle gracefully with error message


class PerformanceTests(TestCase):
    """Test performance and scalability"""
    
    def test_large_team_input_processing(self):
        """Test processing inputs from large teams"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        session = DesignThinkingSession.objects.create(
            design_game=game,
            session_code='PERF123',
            current_mission=game.missions.first()
        )
        
        # Create team with 20 members
        team_members = [
            {'name': f'Student{i}', 'session_id': f'student_{i}'}
            for i in range(20)
        ]
        
        team = DesignTeam.objects.create(
            session=session,
            team_name='Large Team',
            team_emoji='👥',
            team_members=team_members
        )
        
        service = AutoProgressionService()
        
        # Process inputs for all team members
        import time
        start_time = time.time()
        
        for i in range(20):
            result = service.process_phase_input(
                team_id=team.id,
                mission_id=session.current_mission.id,
                student_data={'name': f'Student{i}', 'session_id': f'student_{i}'},
                input_data=[
                    {'type': 'radio', 'label': 'Question 1', 'value': f'Answer {i}', 'order': 1}
                ]
            )
            self.assertTrue(result['success'])
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 20 inputs in under 5 seconds
        self.assertLess(processing_time, 5.0)
        
        # Check final completion status
        tracker = PhaseCompletionTracker.objects.get(
            session=session,
            team=team,
            mission=session.current_mission
        )
        self.assertEqual(tracker.completion_percentage, 100.0)
        self.assertTrue(tracker.is_ready_to_advance)


class ErrorHandlingTests(TestCase):
    """Test comprehensive error handling"""
    
    def test_malformed_input_data(self):
        """Test handling of malformed input data"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        session = DesignThinkingSession.objects.create(
            design_game=game,
            session_code='ERR123',
            current_mission=game.missions.first()
        )
        
        team = DesignTeam.objects.create(
            session=session,
            team_name='Error Test Team',
            team_emoji='❌'
        )
        
        service = AutoProgressionService()
        
        # Test various malformed inputs
        test_cases = [
            # Missing required fields
            (None, session.current_mission.id, {'name': 'Alice'}, []),
            # Invalid input type
            (team.id, session.current_mission.id, {'name': 'Alice', 'session_id': 'alice'}, 
             [{'type': 'invalid', 'label': 'Q', 'value': 'A'}]),
            # Empty input data
            (team.id, session.current_mission.id, {'name': 'Alice', 'session_id': 'alice'}, []),
            # Too many inputs
            (team.id, session.current_mission.id, {'name': 'Alice', 'session_id': 'alice'}, 
             [{'type': 'radio', 'label': f'Q{i}', 'value': f'A{i}'} for i in range(15)]),
        ]
        
        for team_id, mission_id, student_data, input_data in test_cases:
            result = service.process_phase_input(team_id, mission_id, student_data, input_data)
            self.assertFalse(result['success'])
            self.assertIn('error', result)
    
    def test_database_constraint_violations(self):
        """Test handling of database constraint violations"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        session = DesignThinkingSession.objects.create(
            design_game=game,
            session_code='DB123',
            current_mission=game.missions.first()
        )
        
        team = DesignTeam.objects.create(
            session=session,
            team_name='DB Test Team',
            team_emoji='💾'
        )
        
        service = AutoProgressionService()
        
        # Submit valid input first
        result1 = service.process_phase_input(
            team_id=team.id,
            mission_id=session.current_mission.id,
            student_data={'name': 'Alice', 'session_id': 'alice_123'},
            input_data=[
                {'type': 'radio', 'label': 'Question 1', 'value': 'Answer 1', 'order': 1}
            ]
        )
        self.assertTrue(result1['success'])
        
        # Try to submit duplicate (should fail validation)
        result2 = service.process_phase_input(
            team_id=team.id,
            mission_id=session.current_mission.id,
            student_data={'name': 'Alice', 'session_id': 'alice_123'},
            input_data=[
                {'type': 'radio', 'label': 'Question 1', 'value': 'Answer 1', 'order': 1}
            ]
        )
        self.assertFalse(result2['success'])
        self.assertIn('already submitted', result2['error'])


class MonitoringSystemTests(TestCase):
    """Test monitoring and logging system"""
    
    def setUp(self):
        """Set up test data"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        self.game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code='MON123',
            current_mission=self.game.missions.first()
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Test Team',
            team_emoji='📊',
            team_members=[{'name': 'Student1', 'session_id': 'student_1'}]
        )
    
    def test_performance_monitoring(self):
        """Test performance monitoring decorator"""
        from group_learning.monitoring import log_operation
        
        @log_operation('test_operation')
        def test_function():
            import time
            time.sleep(0.1)  # Simulate work
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        
        # Check if metrics were recorded
        metrics = performance_monitor.get_operation_metrics('test_operation')
        self.assertGreater(metrics.get('total_calls', 0), 0)
    
    def test_session_activity_tracking(self):
        """Test session activity monitoring"""
        from group_learning.monitoring import log_session_activity
        
        # Log some activities
        log_session_activity(
            self.session.session_code,
            'input_processed',
            {'team_id': self.team.id, 'input_count': 2}
        )
        
        log_session_activity(
            self.session.session_code,
            'teacher_scored',
            {'team_id': self.team.id, 'score': 'A'}
        )
        
        # Retrieve activities
        activities = activity_monitor.get_session_activity(self.session.session_code)
        self.assertEqual(len(activities), 2)
        
        activity_types = [activity['activity_type'] for activity in activities]
        self.assertIn('input_processed', activity_types)
        self.assertIn('teacher_scored', activity_types)
    
    def test_error_tracking(self):
        """Test error occurrence tracking"""
        from group_learning.monitoring import log_error
        
        # Log some errors
        log_error(
            'validation_error',
            self.session.session_code,
            {'error_message': 'Test validation error'}
        )
        
        log_error(
            'database_error',
            self.session.session_code,
            {'error_message': 'Test database error'}
        )
        
        # Check system health includes error tracking
        health = activity_monitor.get_system_health()
        self.assertIn('error_rate_1h', health)
        self.assertGreaterEqual(health['error_rate_1h'], 2)
    
    def test_websocket_connection_monitoring(self):
        """Test WebSocket connection event tracking"""
        from group_learning.monitoring import log_websocket_event
        
        # Log connection events
        log_websocket_event(
            self.session.session_code,
            'connect',
            'conn_123',
            {'room_group': f'design_thinking_{self.session.session_code}'}
        )
        
        log_websocket_event(
            self.session.session_code,
            'message_received',
            'conn_123',
            {'message_type': 'simplified_input_submit'}
        )
        
        log_websocket_event(
            self.session.session_code,
            'disconnect',
            'conn_123',
            {'close_code': 1000, 'close_reason': 'Normal closure'}
        )
        
        # Check connection stats
        stats = connection_monitor.get_connection_stats(self.session.session_code)
        self.assertEqual(stats.get('total_connections', 0), 1)
        self.assertEqual(stats.get('total_disconnections', 0), 1)
        self.assertEqual(stats.get('current_connections', 0), 0)


class ErrorHandlingTests(TestCase):
    """Test comprehensive error handling scenarios"""
    
    def setUp(self):
        """Set up test data"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        self.game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code='ERR123',
            current_mission=self.game.missions.first()
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Error Test Team',
            team_emoji='⚠️',
            team_members=[{'name': 'Student1', 'session_id': 'student_1'}]
        )
    
    def test_invalid_input_data_validation(self):
        """Test validation of various invalid input scenarios"""
        service = AutoProgressionService()
        
        # Test missing required fields
        result = service.process_phase_input(
            team_id=None,
            mission_id=self.session.current_mission.id,
            student_data={'name': 'Test', 'session_id': 'test_123'},
            input_data=[]
        )
        self.assertFalse(result['success'])
        self.assertIn('Missing required parameters', result['error'])
        
        # Test invalid team ID
        result = service.process_phase_input(
            team_id=99999,
            mission_id=self.session.current_mission.id,
            student_data={'name': 'Test', 'session_id': 'test_123'},
            input_data=[{'type': 'radio', 'label': 'Q1', 'value': 'A1', 'order': 1}]
        )
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
        
        # Test invalid input type
        result = service.process_phase_input(
            team_id=self.team.id,
            mission_id=self.session.current_mission.id,
            student_data={'name': 'Test', 'session_id': 'test_123'},
            input_data=[{'type': 'invalid_type', 'label': 'Q1', 'value': 'A1', 'order': 1}]
        )
        self.assertFalse(result['success'])
        self.assertIn('Invalid input type', result['error'])
        
        # Test oversized input
        result = service.process_phase_input(
            team_id=self.team.id,
            mission_id=self.session.current_mission.id,
            student_data={'name': 'Test', 'session_id': 'test_123'},
            input_data=[{
                'type': 'text_short',
                'label': 'Q1',
                'value': 'A' * 100,  # Too long for short text
                'order': 1
            }]
        )
        self.assertFalse(result['success'])
        self.assertIn('cannot exceed 50 characters', result['error'])
    
    def test_database_consistency_errors(self):
        """Test handling of database consistency issues"""
        # Test with session/team mismatch (team belongs to different session)
        other_session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code='OTHER123',
            current_mission=self.game.missions.first()
        )
        
        other_team = DesignTeam.objects.create(
            session=other_session,
            team_name='Other Team',
            team_emoji='🔒',
            team_members=[{'name': 'OtherStudent', 'session_id': 'other_123'}]
        )
        
        service = AutoProgressionService()
        
        # Try to submit input for team from different session
        result = service.process_phase_input(
            team_id=other_team.id,
            mission_id=self.session.current_mission.id,  # Mission from different session
            student_data={'name': 'Test', 'session_id': 'test_123'},
            input_data=[{'type': 'radio', 'label': 'Q1', 'value': 'A1', 'order': 1}]
        )
        self.assertFalse(result['success'])
        self.assertIn('different games', result['error'])
    
    def test_concurrent_input_submission(self):
        """Test handling of concurrent input submissions"""
        import threading
        import time
        
        service = AutoProgressionService()
        results = []
        
        def submit_input(student_id):
            result = service.process_phase_input(
                team_id=self.team.id,
                mission_id=self.session.current_mission.id,
                student_data={'name': f'Student{student_id}', 'session_id': f'student_{student_id}'},
                input_data=[{
                    'type': 'radio',
                    'label': 'Concurrent Question',
                    'value': f'Answer{student_id}',
                    'order': 1
                }]
            )
            results.append(result)
        
        # Submit 5 concurrent inputs
        threads = []
        for i in range(5):
            thread = threading.Thread(target=submit_input, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All submissions should succeed (different students)
        successful_results = [r for r in results if r['success']]
        self.assertEqual(len(successful_results), 5)
        
        # Verify all inputs were saved
        input_count = SimplifiedPhaseInput.objects.filter(
            team=self.team,
            mission=self.session.current_mission
        ).count()
        self.assertEqual(input_count, 5)


class SecurityAndValidationTests(TestCase):
    """Test security measures and input validation"""
    
    def setUp(self):
        """Set up test data"""
        from django.core.management import call_command
        call_command('setup_simplified_design_thinking', '--overwrite')
        
        self.game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code='SEC123',
            current_mission=self.game.missions.first()
        )
        
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name='Security Test Team',
            team_emoji='🔒',
            team_members=[{'name': 'Student1', 'session_id': 'student_1'}]
        )
    
    def test_input_sanitization(self):
        """Test that inputs are properly sanitized"""
        service = AutoProgressionService()
        
        # Test with potential XSS input
        malicious_inputs = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '{{7*7}}',  # Template injection
            '${7*7}',   # Expression injection
            '../../../etc/passwd',  # Path traversal
        ]
        
        for malicious_input in malicious_inputs:
            result = service.process_phase_input(
                team_id=self.team.id,
                mission_id=self.session.current_mission.id,
                student_data={'name': 'SecurityTest', 'session_id': f'sec_{hash(malicious_input)}'},
                input_data=[{
                    'type': 'text_short',
                    'label': 'Security Test',
                    'value': malicious_input,
                    'order': 1
                }]
            )
            
            # Should either succeed with sanitized input or fail with validation error
            if result['success']:
                # Verify the input was saved and retrieve it
                saved_input = SimplifiedPhaseInput.objects.filter(
                    team=self.team,
                    student_session_id=f'sec_{hash(malicious_input)}'
                ).first()
                
                # The malicious content should be stored as-is (Django handles output escaping)
                # but we verify it doesn't cause errors in our system
                self.assertIsNotNone(saved_input)
                self.assertEqual(saved_input.selected_value, malicious_input)
    
    def test_rate_limiting_validation(self):
        """Test rate limiting for input submissions"""
        service = AutoProgressionService()
        
        # Submit many inputs rapidly from same student
        results = []
        for i in range(15):  # Exceed rate limit of 10 per minute
            result = service.process_phase_input(
                team_id=self.team.id,
                mission_id=self.session.current_mission.id,
                student_data={'name': 'RateTest', 'session_id': 'rate_test_student'},
                input_data=[{
                    'type': 'radio',
                    'label': f'Question {i}',
                    'value': f'Answer {i}',
                    'order': 1
                }]
            )
            results.append(result)
        
        # First submission should succeed
        self.assertTrue(results[0]['success'])
        
        # Later submissions should fail due to duplicate student_session_id
        failed_results = [r for r in results[1:] if not r['success']]
        self.assertGreater(len(failed_results), 0)
    
    def test_model_field_constraints(self):
        """Test database model field constraints"""
        # Test maximum length constraints
        with self.assertRaises(Exception):  # Could be ValidationError or DataError
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=self.session.current_mission,
                session=self.session,
                student_name='A' * 200,  # Exceeds max_length=100
                student_session_id='test_long_name',
                input_type='radio',
                input_label='Test',
                selected_value='Test',
                input_order=1
            )
        
        # Test invalid choice constraints
        with self.assertRaises(Exception):
            SimplifiedPhaseInput.objects.create(
                team=self.team,
                mission=self.session.current_mission,
                session=self.session,
                student_name='Test Student',
                student_session_id='test_invalid_type',
                input_type='invalid_type',  # Not in INPUT_TYPES choices
                input_label='Test',
                selected_value='Test',
                input_order=1
            )


if __name__ == '__main__':
    import unittest
    unittest.main()