"""
Tests for Design Thinking level forms to ensure quest_session handling works correctly.

These tests verify that the QuestSessionFormMixin properly prevents
TypeError: __init__() got multiple values for argument 'quest_session'
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from group_learning.models import (
    DesignThinkingGame,
    DesignThinkingSession,
    DesignMission,
    DesignTeam
)
from group_learning.forms import (
    Level1EmpathyForm,
    Level2DefineForm,
    Level3IdeateForm,
    Level4PrototypeForm,
    Level5ShowcaseForm
)

User = get_user_model()


class QuestSessionFormMixinTestCase(TestCase):
    """Test that forms can be instantiated with quest_session kwarg"""

    def setUp(self):
        """Set up test data"""
        # Create a test game
        self.game = DesignThinkingGame.objects.create(
            title="Test Design Thinking",
            description="Test game",
            auto_advance_enabled=True
        )

        # Create test session (quest_session)
        self.quest_session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code="TEST01",
            status="in_progress",
            is_facilitator_controlled=False
        )

        # Create empathy mission
        self.empathy_mission = DesignMission.objects.create(
            game=self.game,
            title="Empathy Phase",
            mission_type="empathy",
            description="Understand users",
            order=1,
            is_active=True
        )

        # Create define mission
        self.define_mission = DesignMission.objects.create(
            game=self.game,
            title="Define Phase",
            mission_type="define",
            description="Define the problem",
            order=2,
            is_active=True
        )

    def test_level1_form_instantiation_with_quest_session(self):
        """Test Level1EmpathyForm can be instantiated with quest_session"""
        form = Level1EmpathyForm(quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)

    def test_level2_form_instantiation_with_quest_session(self):
        """Test Level2DefineForm can be instantiated with quest_session"""
        form = Level2DefineForm(quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)

    def test_level2_form_instantiation_without_quest_session(self):
        """Test Level2DefineForm can be instantiated without quest_session"""
        form = Level2DefineForm()
        self.assertIsNotNone(form)
        self.assertIsNone(form.quest_session)

    def test_level2_form_with_data_and_quest_session(self):
        """Test Level2DefineForm with both data and quest_session"""
        data = {
            'pov_user': 'Students sitting in the back row of noisy classrooms',
            'pov_need': 'a way to hear the teacher clearly during lessons',
            'pov_insight': 'background noise prevents them from understanding instructions and causes anxiety'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)
        self.assertTrue(form.is_valid(), form.errors)

    def test_level3_form_instantiation_with_quest_session(self):
        """Test Level3IdeateForm can be instantiated with quest_session"""
        form = Level3IdeateForm(quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)

    def test_level4_form_instantiation_with_quest_session(self):
        """Test Level4PrototypeForm can be instantiated with quest_session"""
        form = Level4PrototypeForm(quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)

    def test_level5_form_instantiation_with_quest_session(self):
        """Test Level5ShowcaseForm can be instantiated with quest_session"""
        form = Level5ShowcaseForm(quest_session=self.quest_session)
        self.assertIsNotNone(form)
        self.assertEqual(form.quest_session, self.quest_session)


class Level2DefineFormValidationTestCase(TestCase):
    """Test Level2DefineForm validation logic"""

    def setUp(self):
        """Set up test data"""
        self.game = DesignThinkingGame.objects.create(
            title="Test Game",
            description="Test",
            auto_advance_enabled=True
        )
        self.quest_session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code="TEST02",
            status="in_progress"
        )

    def test_valid_pov_statement(self):
        """Test form with valid POV statement"""
        data = {
            'pov_user': 'Anxious middle school students taking standardized tests',
            'pov_need': 'a way to calm their nerves before the exam starts',
            'pov_insight': 'stress prevents them from recalling studied material effectively'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertTrue(form.is_valid(), form.errors)

    def test_generic_user_rejected(self):
        """Test that generic user terms are rejected"""
        data = {
            'pov_user': 'students',  # Too generic
            'pov_need': 'a way to learn better',
            'pov_insight': 'learning is important for success'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertFalse(form.is_valid())
        self.assertIn('User description is too generic', str(form.errors))

    def test_solution_in_need_rejected(self):
        """Test that solutions in need field are rejected"""
        data = {
            'pov_user': 'Back-row students in large lecture halls',
            'pov_need': 'an app to amplify teacher voice',  # Solution, not need
            'pov_insight': 'they cannot hear the teacher clearly'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertFalse(form.is_valid())
        self.assertIn('should describe what they need, not a specific solution', str(form.errors))

    def test_weak_evidence_rejected(self):
        """Test that weak evidence in insight is rejected"""
        data = {
            'pov_user': 'Distracted elementary students during reading time',
            'pov_need': 'a way to focus better on their books',
            'pov_insight': 'because it would be nice to focus'  # Weak evidence
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertFalse(form.is_valid())
        self.assertIn('should be evidence-based, not opinion-based', str(form.errors))

    def test_get_pov_statement(self):
        """Test POV statement generation"""
        data = {
            'pov_user': 'High school seniors preparing college applications',
            'pov_need': 'clear guidance on essay writing requirements',
            'pov_insight': 'conflicting advice from different sources causes confusion and anxiety'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertTrue(form.is_valid())
        pov = form.get_pov_statement()
        expected = "High school seniors preparing college applications needs clear guidance on essay writing requirements because conflicting advice from different sources causes confusion and anxiety"
        self.assertEqual(pov, expected)

    def test_get_hmw_question(self):
        """Test HMW question generation"""
        data = {
            'pov_user': 'Working parents balancing remote work and childcare',
            'pov_need': 'dedicated quiet time for important video calls',
            'pov_insight': 'interruptions from children damage professional credibility'
        }
        form = Level2DefineForm(data=data, quest_session=self.quest_session)
        self.assertTrue(form.is_valid())
        hmw = form.get_hmw_question()
        expected = "How might we help Working parents balancing remote work and childcare dedicated quiet time for important video calls?"
        self.assertEqual(hmw, expected)


class LevelViewPostTestCase(TestCase):
    """Test LevelView POST handling for Level 2 (Define phase)"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create game
        self.game = DesignThinkingGame.objects.create(
            title="Test Game",
            description="Test",
            auto_advance_enabled=True
        )

        # Create session
        self.session = DesignThinkingSession.objects.create(
            design_game=self.game,
            session_code="TEST03",
            status="in_progress"
        )

        # Create define mission
        self.define_mission = DesignMission.objects.create(
            game=self.game,
            title="Define",
            mission_type="define",
            description="Define the problem",
            order=2,
            is_active=True
        )

        # Set as current mission
        self.session.current_mission = self.define_mission
        self.session.save()

        # Create a team
        self.team = DesignTeam.objects.create(
            session=self.session,
            team_name="Test Team",
            team_emoji="🎯",
            team_color="blue"
        )

    def test_level2_post_returns_success_no_typeerror(self):
        """
        Regression test: POST to level 2 with valid HMW values returns success (no TypeError).

        This test ensures that quest_session is only passed once to the form,
        preventing: TypeError: Level2DefineForm.__init__() got multiple values for argument 'quest_session'
        """
        url = reverse('group_learning:level_submission', kwargs={
            'session_code': self.session.session_code,
            'mission_type': 'define'
        })

        post_data = {
            'pov_user': 'Middle school students in overcrowded classrooms',
            'pov_need': 'individual attention from the teacher during difficult topics',
            'pov_insight': 'lack of personalized support leads to falling behind and losing confidence'
        }

        # Add student name to session to avoid errors
        session = self.client.session
        session['student_name'] = 'Test Student'
        session.save()

        response = self.client.post(url, post_data)

        # Should return JSON success, not 500 error with TypeError
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data.get('success'), f"Response: {response_data}")
        self.assertIn('message', response_data)

    def test_level2_post_with_invalid_data_returns_errors(self):
        """Test that invalid POV data returns validation errors"""
        url = reverse('group_learning:level_submission', kwargs={
            'session_code': self.session.session_code,
            'mission_type': 'define'
        })

        post_data = {
            'pov_user': 'students',  # Too generic
            'pov_need': 'an app',  # Solution, not need
            'pov_insight': 'it would be nice'  # Weak evidence
        }

        response = self.client.post(url, post_data)

        # Should return 400 with validation errors
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertFalse(response_data.get('success'))
        self.assertIn('errors', response_data)

    def test_level2_post_with_nonexistent_session_returns_404(self):
        """Test that posting to nonexistent session returns 404"""
        url = reverse('group_learning:level_submission', kwargs={
            'session_code': 'FAKE99',
            'mission_type': 'define'
        })

        post_data = {
            'pov_user': 'Test user group',
            'pov_need': 'test need',
            'pov_insight': 'test insight'
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 404)

    def test_level2_post_with_invalid_mission_type_returns_400(self):
        """Test that invalid mission type returns 400"""
        url = reverse('group_learning:level_submission', kwargs={
            'session_code': self.session.session_code,
            'mission_type': 'invalid_type'
        })

        post_data = {
            'pov_user': 'Test user',
            'pov_need': 'test need',
            'pov_insight': 'test insight'
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('Invalid mission type', response_data.get('error', ''))
