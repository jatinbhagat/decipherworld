from django import forms
from .models import DemoRequest, SchoolDemoRequest, SchoolReferral

class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = ['name', 'email', 'school', 'country_code', 'mobile_number', 'message']
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
            'country_code': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': '9876543210'
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
            'school_name', 'contact_person', 'email', 'country_code', 'mobile_number', 'city', 
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
            'country_code': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '9876543210'
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


class SchoolReferralForm(forms.ModelForm):
    """Form for school referral program submissions"""
    
    class Meta:
        model = SchoolReferral
        fields = [
            # Referrer Information
            'referrer_name', 'referrer_email', 'referrer_phone', 'referrer_relationship',
            # School Information
            'school_name', 'school_address', 'school_city', 'school_state', 'school_pincode',
            # School Contact Details
            'contact_person_name', 'contact_person_designation', 'contact_person_email', 'contact_person_phone',
            # School Details
            'school_board', 'current_education_programs',
            # Interest and Additional Info
            'interest_level', 'additional_notes'
        ]
        
        widgets = {
            # Referrer Information
            'referrer_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Your full name'
            }),
            'referrer_email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'your.email@example.com'
            }),
            'referrer_phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+91 9999999999'
            }),
            'referrer_relationship': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Parent, Teacher, Principal, Friend'
            }),
            
            # School Information
            'school_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'ABC Public School'
            }),
            'school_address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Complete school address'
            }),
            'school_city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'City name'
            }),
            'school_state': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'State name'
            }),
            'school_pincode': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '123456'
            }),
            
            # School Contact Details
            'contact_person_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Principal or Administrator name'
            }),
            'contact_person_designation': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Principal, Vice Principal, Coordinator'
            }),
            'contact_person_email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'principal@school.edu'
            }),
            'contact_person_phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+91 9999999999'
            }),
            
            # School Details
            'school_board': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'current_education_programs': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Any existing technology or educational programs in use'
            }),
            
            # Interest and Timeline
            'interest_level': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Any additional information about the school or their requirements'
            }),
        }
    
