"""
Tests for Classroom Innovation Quest.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings

from quest_ciq.models import Quest, QuestLevel, Participant, QuestSession, LevelResponse, Leaderboard
from quest_ciq.services.scoring import calculate_level_score, calculate_ideate_bonus, calculate_prototype_bonus, calculate_test_bonus


class QuestModelTests(TestCase):
    """Tests for Quest and related models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.quest = Quest.objects.create(
            title='Test Quest',
            slug='test-quest',
            description='Test description',
            is_active=True
        )

    def test_quest_creation(self):
        """Test creating a quest."""
        self.assertEqual(self.quest.title, 'Test Quest')
        self.assertEqual(self.quest.slug, 'test-quest')
        self.assertTrue(self.quest.is_active)

    def test_quest_level_creation(self):
        """Test creating quest levels."""
        level = QuestLevel.objects.create(
            quest=self.quest,
            order=1,
            name='Test Level',
            short_help='Test help text'
        )
        self.assertEqual(level.order, 1)
        self.assertEqual(level.name, 'Test Level')
        self.assertEqual(level.quest, self.quest)

    def test_participant_creation(self):
        """Test creating a participant."""
        participant = Participant.objects.create(
            user=self.user,
            quest=self.quest,
            is_active=True
        )
        self.assertEqual(participant.user, self.user)
        self.assertEqual(participant.quest, self.quest)
        self.assertTrue(participant.is_active)

    def test_quest_session_creation(self):
        """Test creating a quest session."""
        participant = Participant.objects.create(
            user=self.user,
            quest=self.quest
        )
        session = QuestSession.objects.create(
            participant=participant,
            quest=self.quest
        )
        self.assertEqual(session.participant, participant)
        self.assertEqual(session.total_score, 0)
        self.assertFalse(session.is_frozen)


class SeedCommandTests(TestCase):
    """Tests for seed_ciq management command."""

    def test_seed_command_creates_quest(self):
        """Test that seed_ciq command creates the quest."""
        from django.core.management import call_command
        call_command('seed_ciq')

        quest = Quest.objects.get(slug='classroom-innovation-quest')
        self.assertEqual(quest.title, 'Classroom Innovation Quest')
        self.assertTrue(quest.is_active)

    def test_seed_command_creates_levels(self):
        """Test that seed_ciq command creates 5 levels."""
        from django.core.management import call_command
        call_command('seed_ciq')

        quest = Quest.objects.get(slug='classroom-innovation-quest')
        levels = quest.levels.all()
        self.assertEqual(levels.count(), 5)

        # Check level names
        level_names = [level.name for level in levels.order_by('order')]
        expected_names = ['Empathy', 'Define', 'Ideate', 'Prototype', 'Test']
        self.assertEqual(level_names, expected_names)

    def test_seed_command_idempotent(self):
        """Test that running seed_ciq multiple times is idempotent."""
        from django.core.management import call_command
        call_command('seed_ciq')
        call_command('seed_ciq')  # Run again

        quest_count = Quest.objects.filter(slug='classroom-innovation-quest').count()
        self.assertEqual(quest_count, 1)

        quest = Quest.objects.get(slug='classroom-innovation-quest')
        levels_count = quest.levels.count()
        self.assertEqual(levels_count, 5)


class GatingLogicTests(TestCase):
    """Tests for level gating logic."""

    def setUp(self):
        """Set up test data."""
        from django.core.management import call_command
        call_command('seed_ciq')

        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.quest = Quest.objects.get(slug='classroom-innovation-quest')
        self.participant = Participant.objects.create(user=self.user, quest=self.quest)
        self.session = QuestSession.objects.create(participant=self.participant, quest=self.quest)

    def test_level_1_always_accessible(self):
        """Test that level 1 is always accessible."""
        self.assertTrue(self.session.can_access_level(1))

    def test_cannot_access_level_2_before_level_1(self):
        """Test that level 2 is not accessible before completing level 1."""
        self.assertFalse(self.session.can_access_level(2))

    def test_can_access_level_2_after_level_1(self):
        """Test that level 2 is accessible after completing level 1."""
        level_1 = self.quest.levels.get(order=1)
        LevelResponse.objects.create(
            session=self.session,
            level=level_1,
            answers={'test': 'data'},
            score=10
        )
        self.assertTrue(self.session.can_access_level(2))

    def test_cannot_skip_levels(self):
        """Test that users cannot skip levels."""
        level_1 = self.quest.levels.get(order=1)
        LevelResponse.objects.create(
            session=self.session,
            level=level_1,
            answers={'test': 'data'},
            score=10
        )
        # Should not be able to access level 3 without completing level 2
        self.assertFalse(self.session.can_access_level(3))


class ScoringTests(TestCase):
    """Tests for scoring logic."""

    def setUp(self):
        """Set up test data."""
        from django.core.management import call_command
        call_command('seed_ciq')

        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.quest = Quest.objects.get(slug='classroom-innovation-quest')
        self.participant = Participant.objects.create(user=self.user, quest=self.quest)
        self.session = QuestSession.objects.create(participant=self.participant, quest=self.quest)

    def test_base_score(self):
        """Test that all levels get base score of 10."""
        for order in range(1, 6):
            level = self.quest.levels.get(order=order)
            response = LevelResponse(
                session=self.session,
                level=level,
                answers={}
            )
            score = calculate_level_score(response)
            self.assertGreaterEqual(score, 10)

    def test_ideate_bonus_with_long_text(self):
        """Test Ideate level bonus with long text (>=120 chars)."""
        answers = {
            'ideas_list': 'A' * 120,  # 120 characters
        }
        bonus = calculate_ideate_bonus(answers)
        self.assertEqual(bonus, 10)

    def test_ideate_bonus_with_multiple_items(self):
        """Test Ideate level bonus with multiple items."""
        answers = {
            'ideas_list': 'Idea 1, Idea 2, Idea 3',
        }
        bonus = calculate_ideate_bonus(answers)
        self.assertEqual(bonus, 10)

    def test_ideate_no_bonus_short_text(self):
        """Test Ideate level with no bonus for short text."""
        answers = {
            'ideas_list': 'Short idea',
        }
        bonus = calculate_ideate_bonus(answers)
        self.assertEqual(bonus, 0)

    def test_prototype_bonus_with_link(self):
        """Test Prototype level bonus with link."""
        level = self.quest.levels.get(order=4)
        response = LevelResponse(
            session=self.session,
            level=level,
            answers={'prototype_link': 'https://example.com/prototype'}
        )
        bonus = calculate_prototype_bonus(response.answers, response)
        self.assertEqual(bonus, 10)

    def test_prototype_no_bonus_without_link_or_upload(self):
        """Test Prototype level with no bonus."""
        level = self.quest.levels.get(order=4)
        response = LevelResponse(
            session=self.session,
            level=level,
            answers={}
        )
        bonus = calculate_prototype_bonus(response.answers, response)
        self.assertEqual(bonus, 0)

    def test_test_bonus_with_high_rating(self):
        """Test Test level bonus with rating >= 4."""
        answers = {
            'peer_rating': 4,
        }
        bonus = calculate_test_bonus(answers)
        self.assertEqual(bonus, 10)

        answers = {
            'peer_rating': 5,
        }
        bonus = calculate_test_bonus(answers)
        self.assertEqual(bonus, 10)

    def test_test_no_bonus_with_low_rating(self):
        """Test Test level with no bonus for low rating."""
        answers = {
            'peer_rating': 3,
        }
        bonus = calculate_test_bonus(answers)
        self.assertEqual(bonus, 0)


class LeaderboardTests(TestCase):
    """Tests for leaderboard functionality."""

    def setUp(self):
        """Set up test data."""
        from django.core.management import call_command
        call_command('seed_ciq')

        self.quest = Quest.objects.get(slug='classroom-innovation-quest')

        # Create multiple users and sessions
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.user3 = User.objects.create_user(username='user3', password='pass')

        self.participant1 = Participant.objects.create(user=self.user1, quest=self.quest)
        self.participant2 = Participant.objects.create(user=self.user2, quest=self.quest)
        self.participant3 = Participant.objects.create(user=self.user3, quest=self.quest)

        self.session1 = QuestSession.objects.create(participant=self.participant1, quest=self.quest, total_score=30)
        self.session2 = QuestSession.objects.create(participant=self.participant2, quest=self.quest, total_score=50)
        self.session3 = QuestSession.objects.create(participant=self.participant3, quest=self.quest, total_score=20)

    def test_leaderboard_refresh(self):
        """Test leaderboard refresh creates correct rankings."""
        Leaderboard.refresh_for_quest(self.quest)

        entries = Leaderboard.objects.filter(quest=self.quest).order_by('rank')
        self.assertEqual(entries.count(), 3)

        # Check correct order (highest score first)
        self.assertEqual(entries[0].participant, self.participant2)  # 50 points
        self.assertEqual(entries[1].participant, self.participant1)  # 30 points
        self.assertEqual(entries[2].participant, self.participant3)  # 20 points

        # Check ranks
        self.assertEqual(entries[0].rank, 1)
        self.assertEqual(entries[1].rank, 2)
        self.assertEqual(entries[2].rank, 3)


class FeatureFlagTests(TestCase):
    """Tests for ENABLE_CIQ feature flag."""

    def setUp(self):
        """Set up test data."""
        from django.core.management import call_command
        call_command('seed_ciq')

        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.quest = Quest.objects.get(slug='classroom-innovation-quest')

    def test_quest_accessible_when_enabled(self):
        """Test quest is accessible when ENABLE_CIQ is True."""
        with self.settings(ENABLE_CIQ=True):
            self.client.login(username='testuser', password='testpass123')
            response = self.client.get(
                reverse('quest_ciq:quest_join', kwargs={'slug': 'classroom-innovation-quest'})
            )
            # Should redirect to home after joining
            self.assertEqual(response.status_code, 302)

    def test_quest_404_when_disabled(self):
        """Test quest returns 404 when ENABLE_CIQ is False."""
        with self.settings(ENABLE_CIQ=False):
            # Try to join when feature is disabled - should return 404
            response = self.client.get(
                reverse('quest_ciq:quest_join', kwargs={'slug': 'classroom-innovation-quest'})
            )
            self.assertEqual(response.status_code, 404)


class ViewTests(TestCase):
    """Tests for quest views."""

    def setUp(self):
        """Set up test data."""
        from django.core.management import call_command
        call_command('seed_ciq')

        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.quest = Quest.objects.get(slug='classroom-innovation-quest')

    def test_join_quest_anonymous(self):
        """Test joining a quest anonymously (without login)."""
        response = self.client.get(
            reverse('quest_ciq:quest_join', kwargs={'slug': 'classroom-innovation-quest'})
        )

        # Should create anonymous participant and redirect
        self.assertEqual(response.status_code, 302)
        # Check that a participant was created (user can be None for anonymous)
        self.assertTrue(Participant.objects.filter(quest=self.quest).exists())
        # Check that session ID was saved
        self.assertIn('ciq_session_id', self.client.session)

    def test_join_quest_authenticated(self):
        """Test joining a quest with authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('quest_ciq:quest_join', kwargs={'slug': 'classroom-innovation-quest'})
        )

        # Should create participant linked to user and redirect
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Participant.objects.filter(user=self.user, quest=self.quest).exists()
        )
        # Check that session ID was saved
        self.assertIn('ciq_session_id', self.client.session)

    def test_quest_home_requires_session(self):
        """Test that quest home requires CIQ session."""
        response = self.client.get(
            reverse('quest_ciq:quest_home', kwargs={'slug': 'classroom-innovation-quest'})
        )
        # Should redirect to join page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/join', response.url)

    def test_level_view_requires_session(self):
        """Test that level view requires CIQ session."""
        response = self.client.get(
            reverse('quest_ciq:quest_level', kwargs={'slug': 'classroom-innovation-quest', 'order': 1})
        )
        # Should redirect to join page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/join', response.url)
