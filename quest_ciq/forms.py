"""
Forms for Classroom Innovation Quest levels.
Each form saves to LevelResponse.answers as JSON.
"""
from django import forms
from django.core.validators import URLValidator, FileExtensionValidator
from django.core.exceptions import ValidationError


class EmpathyLevelForm(forms.Form):
    """Level 1: Empathy - Spot a real classroom/user problem."""

    WHO_IS_AFFECTED_CHOICES = [
        ('students', 'Students'),
        ('teacher', 'Teacher'),
        ('both', 'Both'),
    ]

    observed_problem = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Describe the problem you observed...'
        }),
        label='What problem did you observe?',
        help_text='Be specific and clear about the issue.'
    )

    who_is_affected = forms.ChoiceField(
        choices=WHO_IS_AFFECTED_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        label='Who is affected by this problem?'
    )

    why_important = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'Explain why solving this problem matters...'
        }),
        label='Why is this problem important to solve?',
        help_text='Think about the impact on learning and well-being.'
    )


class DefineLevelForm(forms.Form):
    """Level 2: Define - Frame the problem clearly."""

    problem_statement = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'Write a clear problem statement...'
        }),
        label='Problem Statement',
        help_text='Frame the problem in one or two sentences. Be clear and specific.'
    )

    root_causes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'What are the underlying causes of this problem?'
        }),
        label='Root Causes',
        help_text='Identify the underlying factors causing this problem.'
    )


class IdeateLevelForm(forms.Form):
    """Level 3: Ideate - Generate creative solutions."""

    ideas_list = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 5,
            'placeholder': 'List 2-3 creative ideas, separated by commas or new lines...'
        }),
        label='Solution Ideas',
        help_text='List 2-3 ideas, separated by commas or new lines. Aim for at least 120 characters for bonus points!'
    )

    wildcard_idea = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'A wild, out-of-the-box idea...'
        }),
        label='Wildcard Idea (Optional)',
        help_text='Got a crazy idea? Share it here!'
    )


class PrototypeLevelForm(forms.Form):
    """Level 4: Prototype - Create a quick mock/sketch/link."""

    prototype_link = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'https://example.com/my-prototype'
        }),
        label='Prototype Link',
        help_text='Share a link to your prototype, design, or mockup (e.g., Figma, Google Slides, etc.)'
    )

    materials = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Paper, cardboard, digital tools...'
        }),
        label='Materials Used',
        help_text='What materials or tools did you use to create your prototype?'
    )

    one_line_benefit = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'This prototype helps by...'
        }),
        label='Key Benefit',
        help_text='In one line, what is the main benefit of your solution?'
    )

    prototype_upload = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'accept': 'image/jpeg,image/png'
        }),
        label='Prototype Image (Optional)',
        help_text='Upload an image of your prototype (max 2MB, jpg/png only)'
    )

    def clean_prototype_upload(self):
        """Validate file size (max 2MB)."""
        upload = self.cleaned_data.get('prototype_upload')
        if upload:
            if upload.size > 2 * 1024 * 1024:  # 2MB in bytes
                raise ValidationError('File size must be under 2MB.')
        return upload

    def clean(self):
        """Ensure at least one of prototype_link or prototype_upload is provided."""
        cleaned_data = super().clean()
        prototype_link = cleaned_data.get('prototype_link')
        prototype_upload = cleaned_data.get('prototype_upload')

        if not prototype_link and not prototype_upload:
            raise ValidationError(
                'Please provide either a prototype link or upload an image.'
            )

        return cleaned_data


class TestLevelForm(forms.Form):
    """Level 5: Test - Get peer rating and comments."""

    peer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Name of the peer who tested your prototype'
        }),
        label='Peer Tester Name',
        help_text='Who tested your prototype?'
    )

    peer_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '1-5'
        }),
        label='Peer Rating',
        help_text='Rate the prototype from 1 (poor) to 5 (excellent). Bonus points if rating >= 4!'
    )

    peer_comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'What did your peer say about the prototype?'
        }),
        label='Peer Feedback',
        help_text='What feedback did you receive from your peer?'
    )


# Map level order to form class
LEVEL_FORMS = {
    1: EmpathyLevelForm,
    2: DefineLevelForm,
    3: IdeateLevelForm,
    4: PrototypeLevelForm,
    5: TestLevelForm,
}


def get_form_for_level(level_order):
    """
    Get the appropriate form class for a given level order.

    Args:
        level_order: Integer representing the level (1-5)

    Returns:
        Form class or None if level not found
    """
    return LEVEL_FORMS.get(level_order)
