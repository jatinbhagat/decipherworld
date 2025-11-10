from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from unittest.mock import patch

from .models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard
from .services.scoring import calculate_level_score, update_leaderboard, recalculate_ranks
from .feature_flags import get_enable_ciq


class FeatureFlagTests(TestCase):
    """Test feature flag functionality"""

    def test_enable_ciq_default_false(self):
        """Test that ENABLE_CIQ defaults to False"""
        with self.settings(ENABLE_CIQ=None):
            self.assertFalse(get_enable_ciq())

    def test_enable_ciq_when_true(self):
        """Test that ENABLE_CIQ works when set to True"""
        with self.settings(ENABLE_CIQ=True):
            self.assertTrue(get_enable_ciq())

    def test_views_return_404_when_disabled(self):
        """Test that views return 404 when feature is disabled"""
        with self.settings(ENABLE_CIQ=False):
            client = Client()
            response = client.get(reverse('quest_ciq:home'))
            self.assertEqual(response.status_code, 404)


class QuestModelTests(TestCase):
    """Test Quest model"""

    def setUp(self):
        self.quest = Quest.objects.create(
            title="Test Quest",
            description="Test Description",
            slug="test-quest",
            is_active=True
        )

    def test_quest_creation(self):
        """Test creating a quest"""
        self.assertEqual(self.quest.title, "Test Quest")
        self.assertEqual(self.quest.slug, "test-quest")
        self.assertTrue(self.quest.is_active)

    def test_quest_str(self):
        """Test quest string representation"""
        self.assertEqual(str(self.quest), "Test Quest")


class QuestLevelModelTests(TestCase):
    """Test QuestLevel model"""

    def setUp(self):
        self.quest = Quest.objects.create(
            title="Test Quest",
            slug="test-quest"
        )
        self.level = QuestLevel.objects.create(
            quest=self.quest,
            level_number=1,
            title="Level 1",
            description="First level",
            question_text="What is 2+2?",
            max_score=100
        )

    def test_level_creation(self):
        """Test creating a quest level"""
        self.assertEqual(self.level.level_number, 1)
        self.assertEqual(self.level.title, "Level 1")
        self.assertEqual(self.level.max_score, 100)

    def test_level_str(self):
        """Test level string representation"""
        expected = "Test Quest - Level 1: Level 1"
        self.assertEqual(str(self.level), expected)


class ParticipantModelTests(TestCase):
    """Test Participant model"""

    def setUp(self):
        self.participant = Participant.objects.create(
            display_name="Test User",
            email="test@example.com",
            role="student",
            join_code="ABC123XYZ"
        )

    def test_participant_creation(self):
        """Test creating a participant"""
        self.assertEqual(self.participant.display_name, "Test User")
        self.assertEqual(self.participant.role, "student")

    def test_participant_str(self):
        """Test participant string representation"""
        self.assertEqual(str(self.participant), "Test User (student)")


class QuestSessionModelTests(TestCase):
    """Test QuestSession model"""

    def setUp(self):
        self.quest = Quest.objects.create(
            title="Test Quest",
            slug="test-quest"
        )
        self.participant = Participant.objects.create(
            display_name="Test User",
            join_code="ABC123XYZ"
        )
        self.session = QuestSession.objects.create(
            quest=self.quest,
            participant=self.participant
        )

    def test_session_creation(self):
        """Test creating a quest session"""
        self.assertEqual(self.session.status, 'not_started')
        self.assertEqual(self.session.total_score, 0)
        self.assertEqual(self.session.current_level, 1)

    def test_start_session(self):
        """Test starting a session"""
        self.session.start_session()
        self.assertEqual(self.session.status, 'in_progress')
        self.assertIsNotNone(self.session.started_at)

    def test_complete_session(self):
        """Test completing a session"""
        self.session.start_session()
        self.session.complete_session()
        self.assertEqual(self.session.status, 'completed')
        self.assertIsNotNone(self.session.completed_at)


class ScoringServiceTests(TestCase):
    """Test scoring service functions"""

    def setUp(self):
        self.quest = Quest.objects.create(
            title="Test Quest",
            slug="test-quest"
        )
        self.level = QuestLevel.objects.create(
            quest=self.quest,
            level_number=1,
            title="Test Level",
            question_text="Test question",
            max_score=100
        )

    def test_calculate_level_score_empty(self):
        """Test scoring with empty response"""
        score = calculate_level_score("", self.level)
        self.assertEqual(score, 0)

    def test_calculate_level_score_short(self):
        """Test scoring with short response"""
        score = calculate_level_score("Short answer", self.level)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, self.level.max_score)

    def test_calculate_level_score_detailed(self):
        """Test scoring with detailed response"""
        long_response = "This is a very detailed and comprehensive response " * 20
        score = calculate_level_score(long_response, self.level)
        self.assertGreater(score, 50)
        self.assertLessEqual(score, self.level.max_score)


class ViewTests(TestCase):
    """Test views with feature enabled"""

    def setUp(self):
        self.client = Client()
        self.quest = Quest.objects.create(
            title="Test Quest",
            description="Test Description",
            slug="test-quest",
            is_active=True
        )
        QuestLevel.objects.create(
            quest=self.quest,
            level_number=1,
            title="Level 1",
            question_text="Test question",
            max_score=100
        )

    @patch('quest_ciq.feature_flags.get_enable_ciq', return_value=True)
    def test_home_view(self, mock_flag):
        """Test home view renders correctly"""
        response = self.client.get(reverse('quest_ciq:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quest CIQ")

    @patch('quest_ciq.feature_flags.get_enable_ciq', return_value=True)
    def test_join_view_get(self, mock_flag):
        """Test join view GET request"""
        response = self.client.get(reverse('quest_ciq:join', kwargs={'quest_slug': self.quest.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.quest.title)

    @patch('quest_ciq.feature_flags.get_enable_ciq', return_value=True)
    def test_join_view_post(self, mock_flag):
        """Test joining a quest"""
        response = self.client.post(
            reverse('quest_ciq:join', kwargs={'quest_slug': self.quest.slug}),
            {
                'display_name': 'Test Participant',
                'email': 'test@example.com'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after join
        self.assertTrue(Participant.objects.filter(display_name='Test Participant').exists())

    @patch('quest_ciq.feature_flags.get_enable_ciq', return_value=True)
    def test_teacher_dashboard_view(self, mock_flag):
        """Test teacher dashboard view"""
        response = self.client.get(reverse('quest_ciq:teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Dashboard")


class LeaderboardTests(TestCase):
    """Test leaderboard functionality"""

    def setUp(self):
        self.quest = Quest.objects.create(
            title="Test Quest",
            slug="test-quest"
        )
        self.participant1 = Participant.objects.create(
            display_name="User 1",
            join_code="CODE1"
        )
        self.participant2 = Participant.objects.create(
            display_name="User 2",
            join_code="CODE2"
        )
        self.session1 = QuestSession.objects.create(
            quest=self.quest,
            participant=self.participant1,
            total_score=100,
            status='completed'
        )
        self.session2 = QuestSession.objects.create(
            quest=self.quest,
            participant=self.participant2,
            total_score=150,
            status='completed'
        )

    def test_update_leaderboard(self):
        """Test updating leaderboard"""
        update_leaderboard(self.session1)
        update_leaderboard(self.session2)

        leaderboard = Leaderboard.objects.filter(quest=self.quest).order_by('rank')
        self.assertEqual(leaderboard.count(), 2)
        self.assertEqual(leaderboard[0].participant, self.participant2)
        self.assertEqual(leaderboard[0].rank, 1)
        self.assertEqual(leaderboard[1].rank, 2)

    def test_recalculate_ranks(self):
        """Test rank recalculation"""
        Leaderboard.objects.create(
            quest=self.quest,
            participant=self.participant1,
            total_score=100,
            rank=1
        )
        Leaderboard.objects.create(
            quest=self.quest,
            participant=self.participant2,
            total_score=150,
            rank=2
        )

        recalculate_ranks(self.quest)

        leaderboard = Leaderboard.objects.filter(quest=self.quest).order_by('rank')
        self.assertEqual(leaderboard[0].participant, self.participant2)
        self.assertEqual(leaderboard[0].rank, 1)


class IntegrationTests(TestCase):
    """Integration tests for complete quest flow"""

    def setUp(self):
        self.client = Client()
        self.quest = Quest.objects.create(
            title="Integration Test Quest",
            slug="integration-quest",
            is_active=True
        )
        self.level1 = QuestLevel.objects.create(
            quest=self.quest,
            level_number=1,
            title="Level 1",
            question_text="Question 1",
            max_score=100
        )
        self.level2 = QuestLevel.objects.create(
            quest=self.quest,
            level_number=2,
            title="Level 2",
            question_text="Question 2",
            max_score=100
        )

    @patch('quest_ciq.feature_flags.get_enable_ciq', return_value=True)
    def test_complete_quest_flow(self, mock_flag):
        """Test complete flow from join to completion"""
        # Join quest
        response = self.client.post(
            reverse('quest_ciq:join', kwargs={'quest_slug': self.quest.slug}),
            {'display_name': 'Integration Tester', 'email': 'test@example.com'}
        )
        self.assertEqual(response.status_code, 302)

        participant = Participant.objects.get(display_name='Integration Tester')
        session = QuestSession.objects.get(participant=participant, quest=self.quest)

        # Complete level 1
        response = self.client.post(
            reverse('quest_ciq:level', kwargs={'quest_slug': self.quest.slug, 'level_number': 1}),
            {'response_text': 'My answer to level 1'}
        )
        self.assertEqual(response.status_code, 302)

        # Complete level 2
        response = self.client.post(
            reverse('quest_ciq:level', kwargs={'quest_slug': self.quest.slug, 'level_number': 2}),
            {'response_text': 'My answer to level 2'}
        )
        self.assertEqual(response.status_code, 302)

        # Verify session completed
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertEqual(session.level_responses.count(), 2)
