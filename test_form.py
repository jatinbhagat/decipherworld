import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.local')
django.setup()

from core.models import DemoRequest
from core.forms import DemoRequestForm

# Test form creation and validation
print("Testing DemoRequestForm...")

# Test valid form data
form_data = {
    'name': 'Test User',
    'email': 'test@example.com',
    'school': 'Test School',
    'message': 'This is a test message for the demo request.'
}

form = DemoRequestForm(data=form_data)
print(f"Form is valid: {form.is_valid()}")

if form.is_valid():
    print("Form validation passed!")
    # Test saving to database
    try:
        demo_request = form.save()
        print(f"Successfully saved: {demo_request}")
        print(f"ID: {demo_request.id}")
        print(f"Name: {demo_request.name}")
        print(f"Email: {demo_request.email}")
        print(f"School: {demo_request.school}")
        print(f"Created at: {demo_request.created_at}")
    except Exception as e:
        print(f"Error saving to database: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Form validation failed!")
    print("Errors:", form.errors)

print("\nTesting complete.")