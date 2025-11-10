"""
Tests for Classroom Innovation Quest
"""
from django.test import TestCase, Client
from django.urls import reverse
from .models import QuestSession, LevelResponse, CIQSettings
from .forms import (
    Level1EmpathyForm,
    Level2DefineForm,
    Level3IdeateForm,
    Level4PrototypeForm,
    Level5TestForm,
)


class QuestSessionModelTest(TestCase):
    """Test QuestSession model"""

    def setUp(self):
        self.session = QuestSession.objects.create(
            student_name="Test Student"
        )

    def test_session_creation(self):
        """Test that session is created with unique code"""
        self.assertEqual(self.session.student_name, "Test Student")
        self.assertEqual(len(self.session.session_code), 6)
        self.assertEqual(self.session.current_level, 1)
        self.assertEqual(self.session.total_score, 0)

    def test_session_code_uniqueness(self):
        """Test that session codes are unique"""
        session2 = QuestSession.objects.create(student_name="Student 2")
        self.assertNotEqual(self.session.session_code, session2.session_code)

    def test_calculate_score(self):
        """Test score calculation"""
        # Create L1 response
        LevelResponse.objects.create(
            session=self.session,
            level_order=1,
            answers={
                "preset_selected": ["Classroom noise", "Messy desks", "Heavy backpacks"],
                "custom_entered": [],
                "who_is_affected": "students",
                "prioritized": {"top": "Classroom noise", "second": None}
            }
        )

        score = self.session.calculate_score()
        self.assertEqual(score, 10)  # Base 10 for L1

    def test_is_level_accessible(self):
        """Test level accessibility logic"""
        # Level 1 should always be accessible
        self.assertTrue(self.session.is_level_accessible(1))

        # Level 2 should not be accessible without L1 completion
        self.assertFalse(self.session.is_level_accessible(2))

        # Complete L1
        LevelResponse.objects.create(
            session=self.session,
            level_order=1,
            answers={"test": "data"}
        )

        # Now L2 should be accessible
        self.assertTrue(self.session.is_level_accessible(2))


class Level1FormTest(TestCase):
    """Test Level 1 Empathy form"""

    def test_valid_form_min_requirements(self):
        """Test form with minimum valid data"""
        form_data = {
            'preset_pain_points': ['Classroom noise', 'Messy desks', 'Heavy backpacks'],
            'who_is_affected': 'students',
            'top_priority': 'Classroom noise',
        }
        form = Level1EmpathyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_requires_min_3_pain_points(self):
        """Test form requires at least 3 pain points"""
        form_data = {
            'preset_pain_points': ['Classroom noise'],  # Only 1
            'who_is_affected': 'students',
            'top_priority': 'Classroom noise',
        }
        form = Level1EmpathyForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_accepts_custom_pain_points(self):
        """Test form accepts custom pain points"""
        form_data = {
            'preset_pain_points': ['Classroom noise'],
            'custom_pain_1': 'Custom problem 1',
            'custom_pain_2': 'Custom problem 2',
            'who_is_affected': 'students',
            'top_priority': 'Classroom noise',
        }
        form = Level1EmpathyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_top_priority_required(self):
        """Test that top priority is required"""
        form_data = {
            'preset_pain_points': ['Classroom noise', 'Messy desks', 'Heavy backpacks'],
            'who_is_affected': 'students',
            # Missing top_priority
        }
        form = Level1EmpathyForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_top_priority_must_be_in_selected_list(self):
        """Test that top priority must be from selected pain points"""
        form_data = {
            'preset_pain_points': ['Classroom noise', 'Messy desks', 'Heavy backpacks'],
            'who_is_affected': 'students',
            'top_priority': 'Invalid pain point',  # Not in selected list
        }
        form = Level1EmpathyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Top priority must be one of your selected pain points', str(form.errors))


class Level2FormTest(TestCase):
    """Test Level 2 Define form"""

    def test_valid_hmw_statement(self):
        """Test valid HMW statement creation"""
        form_data = {
            'hmw_goal': 'reduce classroom noise',
            'hmw_outcome': 'students can focus better',
        }
        form = Level2DefineForm(data=form_data)
        self.assertTrue(form.is_valid())

        cleaned = form.cleaned_data
        expected = "How might we reduce classroom noise so that students can focus better?"
        self.assertEqual(cleaned['hmw_full'], expected)

    def test_both_fields_required(self):
        """Test both HMW fields are required"""
        form_data = {
            'hmw_goal': 'reduce classroom noise',
            # Missing hmw_outcome
        }
        form = Level2DefineForm(data=form_data)
        self.assertFalse(form.is_valid())


class Level3FormTest(TestCase):
    """Test Level 3 Ideate form"""

    def test_valid_ideas(self):
        """Test form with valid ideas"""
        form_data = {
            'idea_1': 'Install sound-absorbing panels',
            'idea_2': 'Create a quiet zone in the classroom',
            'idea_wild': 'Use noise-canceling headphones for everyone',
        }
        form = Level3IdeateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_requires_min_two_ideas(self):
        """Test form requires at least 2 ideas"""
        form_data = {
            'idea_1': 'Install sound-absorbing panels',
            # Missing idea_2
            'idea_wild': '',
        }
        form = Level3IdeateForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_wild_idea_optional(self):
        """Test that wild idea is optional"""
        form_data = {
            'idea_1': 'Install sound-absorbing panels',
            'idea_2': 'Create a quiet zone',
            # wild idea empty
        }
        form = Level3IdeateForm(data=form_data)
        self.assertTrue(form.is_valid())


class Level4FormTest(TestCase):
    """Test Level 4 Prototype form"""

    def setUp(self):
        self.session = QuestSession.objects.create(student_name="Test Student")
        # Create L3 response with ideas
        LevelResponse.objects.create(
            session=self.session,
            level_order=3,
            answers={
                "ideas": ["Idea 1", "Idea 2", "Wild idea"]
            }
        )

    def test_form_populates_idea_choices(self):
        """Test form populates choices from L3 ideas"""
        form = Level4PrototypeForm(quest_session=self.session)
        self.assertEqual(len(form.fields['selected_idea'].choices), 3)

    def test_valid_prototype_submission(self):
        """Test valid prototype submission"""
        form_data = {
            'selected_idea': '0',
            'one_line_benefit': 'Reduces noise by 50%',
            'materials': 'Cardboard, foam, tape',
        }
        form = Level4PrototypeForm(quest_session=self.session, data=form_data)
        self.assertTrue(form.is_valid())


class Level5FormTest(TestCase):
    """Test Level 5 Test form"""

    def test_valid_feedback(self):
        """Test valid feedback submission"""
        form_data = {
            'peer_name': 'John Doe',
            'peer_rating': '4',
            'peer_comment': 'Great prototype!',
            'feedback_surprise': 'The simplicity was praised',
        }
        form = Level5TestForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['peer_rating'], 4)

    def test_rating_required(self):
        """Test that rating is required"""
        form_data = {
            'peer_name': 'John Doe',
            # Missing rating
        }
        form = Level5TestForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewsTest(TestCase):
    """Test quest_ciq views"""

    def setUp(self):
        self.client = Client()
        CIQSettings.objects.create(enable_ciq=True)

    def test_home_view(self):
        """Test home view loads"""
        response = self.client.get(reverse('quest_ciq:home'))
        self.assertEqual(response.status_code, 200)

    def test_join_view_get(self):
        """Test join view GET"""
        response = self.client.get(reverse('quest_ciq:join'))
        self.assertEqual(response.status_code, 200)

    def test_join_view_post_creates_session(self):
        """Test join view POST creates session"""
        response = self.client.post(reverse('quest_ciq:join'), {
            'student_name': 'Test Student'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(QuestSession.objects.filter(student_name='Test Student').exists())

    def test_level_view_requires_previous_completion(self):
        """Test that level 2 requires level 1 completion"""
        session = QuestSession.objects.create(student_name="Test Student")

        # Try to access L2 without completing L1
        response = self.client.get(
            reverse('quest_ciq:level', kwargs={
                'session_code': session.session_code,
                'level_order': 2
            })
        )
        self.assertEqual(response.status_code, 302)  # Should redirect

    def test_leaderboard_view(self):
        """Test leaderboard view"""
        response = self.client.get(reverse('quest_ciq:leaderboard'))
        self.assertEqual(response.status_code, 200)


class ScoringTest(TestCase):
    """Test scoring logic"""

    def setUp(self):
        self.session = QuestSession.objects.create(student_name="Test Student")

    def test_base_scoring(self):
        """Test base scoring (+10 per level)"""
        # Create responses for all 5 levels
        for i in range(1, 6):
            LevelResponse.objects.create(
                session=self.session,
                level_order=i,
                answers={"test": "data"}
            )

        score = self.session.calculate_score()
        self.assertEqual(score, 50)  # 10 * 5 levels

    def test_l3_bonus_for_ideas(self):
        """Test L3 bonus for 2+ ideas"""
        LevelResponse.objects.create(
            session=self.session,
            level_order=3,
            answers={
                "ideas": ["Idea 1", "Idea 2", ""]
            }
        )

        score = self.session.calculate_score()
        self.assertGreaterEqual(score, 20)  # Base 10 + bonus 10

    def test_l5_bonus_for_high_rating(self):
        """Test L5 bonus for rating ≥4"""
        LevelResponse.objects.create(
            session=self.session,
            level_order=5,
            answers={
                "peer_rating": 5
            }
        )

        score = self.session.calculate_score()
        self.assertEqual(score, 20)  # Base 10 + bonus 10
