from django import forms
from .models import Participant, LevelResponse, Quest, QuestLevel


class JoinQuestForm(forms.ModelForm):
    """Form for participants to join a quest"""
    class Meta:
        model = Participant
        fields = ['display_name', 'email']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your email (optional)',
            }),
        }
        labels = {
            'display_name': 'Your Name',
            'email': 'Email Address',
        }


class LevelResponseForm(forms.ModelForm):
    """Form for submitting a level response"""
    class Meta:
        model = LevelResponse
        fields = ['response_text']
        widgets = {
            'response_text': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-32',
                'placeholder': 'Enter your response here...',
                'required': True,
            }),
        }
        labels = {
            'response_text': 'Your Response',
        }


class QuestCreationForm(forms.ModelForm):
    """Form for teachers to create a new quest"""
    class Meta:
        model = Quest
        fields = ['title', 'description', 'slug', 'max_participants']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Quest Title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-24',
                'placeholder': 'Describe your quest...',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'quest-slug',
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Leave empty for unlimited',
                'min': 1,
            }),
        }
        labels = {
            'title': 'Quest Title',
            'description': 'Description',
            'slug': 'URL Slug',
            'max_participants': 'Max Participants',
        }


class QuestLevelForm(forms.ModelForm):
    """Form for teachers to create/edit quest levels"""
    class Meta:
        model = QuestLevel
        fields = ['level_number', 'title', 'description', 'question_text', 'max_score', 'time_limit_minutes']
        widgets = {
            'level_number': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 1,
            }),
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Level Title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-20',
                'placeholder': 'Level description...',
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-32',
                'placeholder': 'Enter the question or challenge...',
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Leave empty for no time limit',
                'min': 1,
            }),
        }
        labels = {
            'level_number': 'Level Number',
            'title': 'Level Title',
            'description': 'Description',
            'question_text': 'Question/Challenge',
            'max_score': 'Maximum Score',
            'time_limit_minutes': 'Time Limit (minutes)',
        }
