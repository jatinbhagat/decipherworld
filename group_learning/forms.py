"""
Forms for Design Thinking / Quest CIQ mission levels.

These forms handle student input for different phases of the Design Thinking process.
Each form uses the QuestSessionFormMixin to properly inject quest_session without
causing duplicate argument errors.
"""

from django import forms
from .forms_mixins import QuestSessionFormMixin
from .models import SimplifiedPhaseInput


class Level1EmpathyForm(QuestSessionFormMixin, forms.Form):
    """
    Level 1: Empathy Phase
    Captures user observations and emotional insights.
    """

    user_persona_name = forms.CharField(
        max_length=100,
        required=True,
        label="User Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Sarah, the back-row student',
            'class': 'observation-input'
        })
    )

    user_persona_age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        label="Age",
        widget=forms.NumberInput(attrs={
            'placeholder': '14',
            'class': 'observation-input'
        })
    )

    user_persona_role = forms.CharField(
        max_length=100,
        required=True,
        label="Role",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., middle school student',
            'class': 'observation-input'
        })
    )

    problem_category = forms.CharField(
        max_length=200,
        required=True,
        label="Problem Category",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., classroom learning challenges',
            'class': 'observation-input'
        })
    )

    observation_what = forms.CharField(
        max_length=200,
        required=True,
        label="What did you observe?",
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe what you saw the user doing...',
            'class': 'observation-input',
            'rows': 3
        })
    )

    observation_emotion = forms.ChoiceField(
        required=True,
        label="What emotion did you observe?",
        choices=[
            ('frustrated', 'Frustrated'),
            ('confused', 'Confused'),
            ('anxious', 'Anxious'),
            ('bored', 'Bored'),
            ('overwhelmed', 'Overwhelmed'),
            ('excited', 'Excited'),
            ('focused', 'Focused'),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.quest_session is available here from the mixin


class Level2DefineForm(QuestSessionFormMixin, forms.Form):
    """
    Level 2: Define Phase (HMW / POV Statement)
    Creates Point of View statements and How Might We questions.

    Uses empathy data from Level 1 to suggest HMW transformations.
    """

    pov_user = forms.CharField(
        max_length=100,
        required=True,
        label="WHO is your specific user?",
        widget=forms.TextInput(attrs={
            'id': 'pov-user',
            'class': 'pov-input',
            'placeholder': 'e.g., Students who sit in the back of noisy classrooms',
            'maxlength': 100
        }),
        help_text="Be specific! Avoid generic terms like 'students' or 'people'"
    )

    pov_need = forms.CharField(
        max_length=120,
        required=True,
        label="WHAT do they need?",
        widget=forms.TextInput(attrs={
            'id': 'pov-need',
            'class': 'pov-input',
            'placeholder': 'e.g., a way to hear the teacher clearly during lessons',
            'maxlength': 120
        }),
        help_text="Focus on the need, not a solution! Avoid mentioning specific products or tools"
    )

    pov_insight = forms.CharField(
        max_length=150,
        required=True,
        label="WHY do they need this?",
        widget=forms.TextInput(attrs={
            'id': 'pov-insight',
            'class': 'pov-input',
            'placeholder': 'e.g., because background noise prevents them from understanding instructions',
            'maxlength': 150
        }),
        help_text="Base this on what you actually observed in your empathy research"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.quest_session is available here from the mixin
        # Can use it to load L1 data for suggested HMW
        self._load_empathy_suggestions()

    def _load_empathy_suggestions(self):
        """
        Load Level 1 empathy data to provide suggested POV components.
        This helps students build on their previous work.
        """
        if not self.quest_session:
            return

        # Retrieve L1 empathy inputs from the session
        # This logic remains unchanged from existing implementation
        try:
            empathy_inputs = SimplifiedPhaseInput.objects.filter(
                session=self.quest_session,
                mission__mission_type='empathy'
            ).order_by('-submitted_at')[:3]

            if empathy_inputs.exists():
                # Store suggestions for potential use in template context
                self.empathy_suggestions = [
                    {
                        'user': inp.content.get('user_persona_name', ''),
                        'observation': inp.content.get('observation_what', ''),
                        'emotion': inp.content.get('observation_emotion', '')
                    }
                    for inp in empathy_inputs
                    if isinstance(inp.content, dict)
                ]
        except Exception:
            # Fail gracefully if empathy data unavailable
            self.empathy_suggestions = []

    def clean(self):
        """Validate POV statement quality"""
        cleaned_data = super().clean()
        user = cleaned_data.get('pov_user', '').lower()
        need = cleaned_data.get('pov_need', '').lower()
        insight = cleaned_data.get('pov_insight', '').lower()

        # Check for overly generic user
        generic_terms = ['people', 'everyone', 'users', 'students', 'teachers']
        if any(term == user for term in generic_terms):
            raise forms.ValidationError(
                "User description is too generic. Be more specific about who you observed."
            )

        # Check for solutions in needs
        solution_keywords = ['app', 'phone', 'website', 'tablet', 'computer', 'device', 'tool']
        if any(keyword in need for keyword in solution_keywords):
            raise forms.ValidationError(
                "The 'need' field should describe what they need, not a specific solution."
            )

        # Check for weak evidence
        weak_evidence = ['cool', 'nice', 'good', 'better', 'awesome', 'fun', 'would be']
        if any(word in insight for word in weak_evidence):
            raise forms.ValidationError(
                "Insight should be evidence-based, not opinion-based. Use what you observed."
            )

        return cleaned_data

    def get_pov_statement(self):
        """Generate the full POV statement from form data"""
        if not self.is_valid():
            return None
        data = self.cleaned_data
        return f"{data['pov_user']} needs {data['pov_need']} because {data['pov_insight']}"

    def get_hmw_question(self):
        """Generate How Might We question from POV"""
        if not self.is_valid():
            return None
        data = self.cleaned_data
        return f"How might we help {data['pov_user']} {data['pov_need']}?"


class Level3IdeateForm(QuestSessionFormMixin, forms.Form):
    """
    Level 3: Ideate Phase
    Generates and evaluates solution ideas based on POV/HMW.
    """

    idea_title = forms.CharField(
        max_length=100,
        required=True,
        label="Solution Idea Title",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Classroom Noise Canceller',
            'class': 'ideate-input'
        })
    )

    idea_description = forms.CharField(
        max_length=500,
        required=True,
        label="How does your idea work?",
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe your solution idea in detail...',
            'class': 'ideate-input',
            'rows': 4
        })
    )

    idea_feasibility = forms.ChoiceField(
        required=True,
        label="How feasible is this idea?",
        choices=[
            ('1', 'Very difficult - needs lots of resources'),
            ('2', 'Somewhat difficult - needs some help'),
            ('3', 'Moderate - doable with effort'),
            ('4', 'Fairly easy - can do with basic resources'),
            ('5', 'Very easy - can start right away'),
        ]
    )

    idea_impact = forms.ChoiceField(
        required=True,
        label="How much impact would this have?",
        choices=[
            ('1', 'Minimal - helps a little'),
            ('2', 'Small - helps some'),
            ('3', 'Moderate - noticeable improvement'),
            ('4', 'Large - significant improvement'),
            ('5', 'Huge - transformative solution'),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.quest_session is available here from the mixin


class Level4PrototypeForm(QuestSessionFormMixin, forms.Form):
    """
    Level 4: Prototype Phase
    Documents prototype creation and testing plan.
    """

    prototype_type = forms.ChoiceField(
        required=True,
        label="What type of prototype did you create?",
        choices=[
            ('sketch', 'Sketch/Drawing'),
            ('model', 'Physical Model'),
            ('storyboard', 'Storyboard'),
            ('roleplay', 'Role-play/Acting'),
            ('digital', 'Digital Mockup'),
        ]
    )

    prototype_description = forms.CharField(
        max_length=500,
        required=True,
        label="Describe your prototype",
        widget=forms.Textarea(attrs={
            'placeholder': 'What did you create and how does it demonstrate your idea?',
            'class': 'prototype-input',
            'rows': 4
        })
    )

    testing_plan = forms.CharField(
        max_length=300,
        required=True,
        label="How will you test this with users?",
        widget=forms.Textarea(attrs={
            'placeholder': 'What questions will you ask? What will you observe?',
            'class': 'prototype-input',
            'rows': 3
        })
    )

    feedback_received = forms.CharField(
        max_length=500,
        required=False,
        label="User Feedback (if tested)",
        widget=forms.Textarea(attrs={
            'placeholder': 'What did users say about your prototype?',
            'class': 'prototype-input',
            'rows': 3
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.quest_session is available here from the mixin


class Level5ShowcaseForm(QuestSessionFormMixin, forms.Form):
    """
    Level 5: Showcase/Test Phase
    Final presentation and reflection on the design process.
    """

    presentation_summary = forms.CharField(
        max_length=500,
        required=True,
        label="Summarize your solution",
        widget=forms.Textarea(attrs={
            'placeholder': 'Brief overview of your final solution...',
            'class': 'showcase-input',
            'rows': 4
        })
    )

    key_learnings = forms.CharField(
        max_length=400,
        required=True,
        label="What did you learn from this process?",
        widget=forms.Textarea(attrs={
            'placeholder': 'Reflect on your design thinking journey...',
            'class': 'showcase-input',
            'rows': 3
        })
    )

    would_change = forms.CharField(
        max_length=300,
        required=False,
        label="What would you do differently?",
        widget=forms.Textarea(attrs={
            'placeholder': 'If you could start over, what would you change?',
            'class': 'showcase-input',
            'rows': 3
        })
    )

    real_world_application = forms.CharField(
        max_length=300,
        required=True,
        label="How could you apply design thinking to other problems?",
        widget=forms.Textarea(attrs={
            'placeholder': 'Where else could you use these skills?',
            'class': 'showcase-input',
            'rows': 3
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.quest_session is available here from the mixin
