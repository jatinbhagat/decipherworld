from django import forms
from .models import DemoRequest

class DemoRequestForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('principal', 'Principal'),
        ('vice_principal', 'Vice Principal'),
        ('academic_head', 'Academic Head'),
        ('teacher', 'Teacher'),
        ('it_administrator', 'IT Administrator'),
        ('other', 'Other'),
    ]
    
    STUDENT_COUNT_CHOICES = [
        ('under_100', 'Under 100'),
        ('100_500', '100-500'),
        ('500_1000', '500-1000'),
        ('1000_plus', '1000+'),
    ]
    
    INTEREST_CHOICES = [
        ('student_platform', 'Student Game Platform'),
        ('ai_teacher_tools', 'AI Teacher Tools'),
        ('both', 'Both'),
        ('custom_training', 'Custom Training'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
        })
    )
    
    student_count_range = forms.ChoiceField(
        choices=STUDENT_COUNT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
        })
    )
    
    interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        })
    )
    
    class Meta:
        model = DemoRequest
        fields = [
            'full_name', 'email', 'phone', 'school_name', 'role',
            'student_count_range', 'interests', 'message', 'preferred_demo_date'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'your.email@school.edu'
            }),
            'school_name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your school or institution name'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 4,
                'placeholder': 'Tell us about your goals and what you\'d like to see in the demo...'
            }),
            'preferred_demo_date': forms.DateInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'type': 'date'
            }),
        }