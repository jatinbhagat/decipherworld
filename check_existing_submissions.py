#!/usr/bin/env python3
"""
Check existing submissions to understand the structure
"""

import os
import sys

# Add Django project to path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

import django
django.setup()

from group_learning.models import SimplifiedPhaseInput

def check_submissions():
    submissions = SimplifiedPhaseInput.objects.all()
    print(f"Found {submissions.count()} existing submissions")
    
    for submission in submissions[:3]:
        print(f"\nSubmission ID: {submission.id}")
        print(f"  Team: {submission.team}")
        print(f"  Mission: {submission.mission}")
        print(f"  Student Name: {submission.student_name}")
        print(f"  Input Label: {submission.input_label}")
        print(f"  Selected Value: {submission.selected_value[:100]}...")
        print(f"  Teacher Score: {submission.teacher_score}")
        
        # Print all field values
        for field in submission._meta.fields:
            value = getattr(submission, field.name)
            print(f"  {field.name}: {value}")

if __name__ == "__main__":
    check_submissions()