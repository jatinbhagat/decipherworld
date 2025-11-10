"""
Forms for Classroom Innovation Quest levels
Each level has specific form fields and validation
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import QuestSession, LevelResponse
from .constants import CLASSROOM_PAIN_POINTS, WHO_AFFECTED_CHOICES, EMOJI_RATINGS


class JoinQuestForm(forms.Form):
    """Form for students to join/create a quest session"""
    student_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your name',
            'required': True,
        }),
        label="Your Name"
    )


class Level1EmpathyForm(forms.Form):
    """
    Level 1: Empathy - Pain points with prioritization
    """
    # Preset pain points (multi-select checkboxes)
    preset_pain_points = forms.MultipleChoiceField(
        choices=[(p, p) for p in CLASSROOM_PAIN_POINTS],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary',
        }),
        required=False,
        label="Select classroom pain points"
    )

    # Custom pain points (3 optional fields)
    custom_pain_1 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Add your own pain point (optional)',
        }),
        label="Custom pain point 1"
    )

    custom_pain_2 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Add another pain point (optional)',
        }),
        label="Custom pain point 2"
    )

    custom_pain_3 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Add one more pain point (optional)',
        }),
        label="Custom pain point 3"
    )

    # Who is affected
    who_is_affected = forms.ChoiceField(
        choices=WHO_AFFECTED_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'radio radio-primary',
        }),
        label="Who is affected by these problems?",
        initial='students'
    )

    # Prioritization dropdowns (populated dynamically via JS)
    top_priority = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
        }),
        label="Pick your TOP pain point"
    )

    second_priority = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
        }),
        label="Pick second priority (optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Priority choices will be populated dynamically via JavaScript
        # based on selected preset + custom entries

    def clean(self):
        cleaned_data = super().clean()

        # Collect all pain points
        preset_selected = cleaned_data.get('preset_pain_points', [])
        custom_1 = (cleaned_data.get('custom_pain_1') or '').strip()
        custom_2 = (cleaned_data.get('custom_pain_2') or '').strip()
        custom_3 = (cleaned_data.get('custom_pain_3') or '').strip()

        custom_entered = [c for c in [custom_1, custom_2, custom_3] if c]

        # Validate minimum 3 total pain points
        total_count = len(preset_selected) + len(custom_entered)
        if total_count < 3:
            raise ValidationError(
                "Please select or enter at least 3 pain points total."
            )

        # Validate top priority is selected
        top = cleaned_data.get('top_priority')
        if not top:
            raise ValidationError("Please select your top priority pain point.")

        # Validate second priority doesn't duplicate top
        second = cleaned_data.get('second_priority')
        if second and second == top:
            raise ValidationError(
                "Second priority must be different from top priority."
            )

        # Store structured data
        cleaned_data['all_pain_points'] = list(preset_selected) + custom_entered
        cleaned_data['custom_list'] = custom_entered

        return cleaned_data

    def get_answers_json(self):
        """Convert form data to JSON structure for storage"""
        cleaned = self.cleaned_data
        return {
            "preset_selected": list(cleaned.get('preset_pain_points', [])),
            "custom_entered": cleaned.get('custom_list', []),
            "who_is_affected": cleaned.get('who_is_affected'),
            "prioritized": {
                "top": cleaned.get('top_priority'),
                "second": cleaned.get('second_priority') or None,
            }
        }


class Level2DefineForm(forms.Form):
    """
    Level 2: Define - How Might We statement builder
    """
    hmw_goal = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'help students stay focused',
        }),
        label="How might we..."
    )

    hmw_outcome = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'so that lessons are easier to follow',
        }),
        label="so that..."
    )

    def __init__(self, quest_session=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quest_session = quest_session

        # Load L1 response for suggestions
        if quest_session:
            try:
                l1_response = LevelResponse.objects.get(
                    session=quest_session,
                    level_order=1
                )
                self.l1_answers = l1_response.get_answers()
            except LevelResponse.DoesNotExist:
                self.l1_answers = {}

    def clean(self):
        cleaned_data = super().clean()

        goal = (cleaned_data.get('hmw_goal') or '').strip()
        outcome = (cleaned_data.get('hmw_outcome') or '').strip()

        if not goal:
            raise ValidationError("Please complete the 'How might we' goal.")

        if not outcome:
            raise ValidationError("Please complete the 'so that' outcome.")

        # Compose full HMW statement
        cleaned_data['hmw_full'] = f"How might we {goal} so that {outcome}?"

        return cleaned_data

    def get_answers_json(self):
        """Convert form data to JSON structure for storage"""
        cleaned = self.cleaned_data
        return {
            "hmw_goal": cleaned.get('hmw_goal'),
            "hmw_outcome": cleaned.get('hmw_outcome'),
            "hmw_full": cleaned.get('hmw_full'),
        }


class Level3IdeateForm(forms.Form):
    """
    Level 3: Ideate - Three idea boxes (2 required, 1 wild optional)
    """
    idea_1 = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'Describe your first idea...',
            'rows': 3,
        }),
        label="Idea 1"
    )

    idea_2 = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'Describe your second idea...',
            'rows': 3,
        }),
        label="Idea 2"
    )

    idea_wild = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'Add a wild, creative idea! 💡',
            'rows': 3,
        }),
        label="Wild idea 💡 (optional)"
    )

    def clean(self):
        cleaned_data = super().clean()

        idea_1 = (cleaned_data.get('idea_1') or '').strip()
        idea_2 = (cleaned_data.get('idea_2') or '').strip()
        idea_wild = (cleaned_data.get('idea_wild') or '').strip()

        # Validate at least 2 non-empty ideas
        non_empty = [i for i in [idea_1, idea_2] if i]
        if len(non_empty) < 2:
            raise ValidationError("Please provide at least 2 ideas.")

        # Store as list
        cleaned_data['ideas_list'] = [idea_1, idea_2, idea_wild]

        return cleaned_data

    def get_answers_json(self):
        """Convert form data to JSON structure for storage"""
        cleaned = self.cleaned_data
        return {
            "ideas": cleaned.get('ideas_list', []),
        }


class Level4PrototypeForm(forms.Form):
    """
    Level 4: Prototype - Select one idea and describe prototype
    """
    selected_idea = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'radio radio-primary',
        }),
        label="Select the idea you want to prototype"
    )

    prototype_explanation = forms.CharField(
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'Explain your prototype in 2-3 sentences...',
            'rows': 4,
        }),
        label="Explain your prototype",
        help_text="Describe what it is, how it works, and why it solves the problem (2-3 sentences)"
    )

    prototype_link = forms.URLField(
        max_length=500,
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'https://... (optional)',
        }),
        label="Prototype link (optional)"
    )

    materials = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'What materials did you use?',
            'rows': 3,
        }),
        label="Materials used (optional)"
    )

    one_line_benefit = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'In one sentence, what problem does this solve?',
        }),
        label="One-line benefit (optional)"
    )

    prototype_upload = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/jpeg,image/png',
        }),
        label="Upload prototype image (optional, max 2MB)",
        help_text="JPG or PNG, max 2MB"
    )

    def __init__(self, quest_session=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quest_session = quest_session

        # Load L3 ideas for selection
        if quest_session:
            try:
                l3_response = LevelResponse.objects.get(
                    session=quest_session,
                    level_order=3
                )
                l3_answers = l3_response.get_answers()
                ideas = l3_answers.get('ideas', [])

                # Build choices from non-empty ideas
                choices = []
                for idx, idea in enumerate(ideas):
                    if idea.strip():
                        # Truncate for display
                        display_text = idea[:60] + '...' if len(idea) > 60 else idea
                        choices.append((str(idx), display_text))

                self.fields['selected_idea'].choices = choices
                self.l3_ideas = ideas

            except LevelResponse.DoesNotExist:
                self.fields['selected_idea'].choices = []
                self.l3_ideas = []

    def clean_prototype_upload(self):
        upload = self.cleaned_data.get('prototype_upload')
        if upload:
            # Validate file size (2MB max)
            if upload.size > 2 * 1024 * 1024:
                raise ValidationError("File size must be under 2MB.")
        return upload

    def clean(self):
        cleaned_data = super().clean()

        # Validate selected idea exists in L3
        selected_idx = cleaned_data.get('selected_idea')
        if selected_idx is not None:
            try:
                idx = int(selected_idx)
                if hasattr(self, 'l3_ideas') and 0 <= idx < len(self.l3_ideas):
                    cleaned_data['selected_idea_text'] = self.l3_ideas[idx]
                    cleaned_data['selected_idea_index'] = idx
                else:
                    raise ValidationError("Invalid idea selection.")
            except (ValueError, TypeError):
                raise ValidationError("Invalid idea selection.")

        return cleaned_data

    def get_answers_json(self):
        """Convert form data to JSON structure for storage"""
        cleaned = self.cleaned_data
        upload = cleaned.get('prototype_upload')

        return {
            "selected_idea_index": cleaned.get('selected_idea_index'),
            "selected_idea_text": cleaned.get('selected_idea_text'),
            "prototype_explanation": cleaned.get('prototype_explanation', ''),
            "prototype_link": cleaned.get('prototype_link', ''),
            "materials": cleaned.get('materials', ''),
            "one_line_benefit": cleaned.get('one_line_benefit', ''),
            "prototype_upload": upload.name if upload else None,
        }


class Level5TestForm(forms.Form):
    """
    Level 5: Test - Emoji rating + reflection
    """
    peer_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Who gave you feedback?',
        }),
        label="Peer name"
    )

    peer_rating = forms.ChoiceField(
        choices=[(str(r[0]), f"{r[1]} {r[2]}") for r in EMOJI_RATINGS],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'rating-emoji',
        }),
        label="How did they rate your prototype?"
    )

    peer_comment = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'What did they say?',
            'rows': 4,
        }),
        label="Feedback comment (optional)"
    )

    feedback_surprise = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'What surprised you about the feedback?',
        }),
        label="What feedback surprised you? (optional)"
    )

    def clean_peer_rating(self):
        rating = self.cleaned_data.get('peer_rating')
        try:
            rating_int = int(rating)
            if not (1 <= rating_int <= 5):
                raise ValidationError("Rating must be between 1 and 5.")
            return rating_int
        except (ValueError, TypeError):
            raise ValidationError("Invalid rating value.")

    def get_answers_json(self):
        """Convert form data to JSON structure for storage"""
        cleaned = self.cleaned_data
        return {
            "peer_name": cleaned.get('peer_name'),
            "peer_rating": cleaned.get('peer_rating'),
            "peer_comment": cleaned.get('peer_comment', ''),
            "feedback_surprise": cleaned.get('feedback_surprise', ''),
        }
