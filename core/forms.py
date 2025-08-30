from django import forms
from .models import DemoRequest, SchoolDemoRequest

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


class SchoolDemoRequestForm(forms.ModelForm):
    PRODUCT_CHOICES = [
        ('entrepreneurship', 'Entrepreneurship Course'),
        ('ai_course', 'AI Course for Students'),
        ('financial_literacy', 'Financial Literacy Course'),
        ('climate_change', 'Climate Change Course'),
        ('teacher_training', 'AI Training for Teachers'),
    ]
    
    interested_products = forms.MultipleChoiceField(
        choices=PRODUCT_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox text-primary focus:ring-primary border-gray-300 rounded'
        }),
        required=True,
        label="Products of Interest (Select all that apply)"
    )
    
    class Meta:
        model = SchoolDemoRequest
        fields = [
            'school_name', 'contact_person', 'email', 'phone', 'city', 
            'student_count', 'interested_products', 'additional_requirements', 
            'preferred_demo_time'
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your school name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Principal/Administrator name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'admin@school.edu'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+91 98765 43210'
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your city'
            }),
            'student_count': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '500',
                'min': '1'
            }),
            'additional_requirements': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Any specific requirements, questions, or goals for implementation...'
            }),
            'preferred_demo_time': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Weekdays 2-4 PM, Next week, etc.'
            }),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert the selected products to a list for JSONField
        instance.interested_products = self.cleaned_data['interested_products']
        if commit:
            instance.save()
        return instance