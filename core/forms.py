from django import forms
from .models import DemoRequest

class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = ['name', 'email', 'school', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'your.email@school.edu'
            }),
            'school': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Your school or institution name'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 4,
                'placeholder': 'Tell us about your goals and what you\'d like to see in the demo...'
            }),
        }