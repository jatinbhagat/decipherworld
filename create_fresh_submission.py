#!/usr/bin/env python3
"""
Create a fresh unscored submission for testing
"""

import os
import sys

# Add Django project to path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

import django
django.setup()

from group_learning.models import DesignThinkingSession, DesignTeam, SimplifiedPhaseInput, DesignMission

def create_fresh_submission():
    session_code = "G03KHM"
    
    try:
        session = DesignThinkingSession.objects.get(session_code=session_code)
        team = DesignTeam.objects.filter(session=session).first()
        
        if not team:
            print("❌ No teams found")
            return False
            
        # Get an existing mission
        mission = DesignMission.objects.first()
        if not mission:
            print("❌ No missions found")
            return False
        
        # Create a fresh unscored submission
        submission = SimplifiedPhaseInput.objects.create(
            team=team,
            mission=mission,
            student_name='Test Student Alpha',
            selected_value='We could implement a smart notification system that learns user preferences and only shows relevant alerts, reducing information overload.',
            input_label='Creative Solution'
        )
        
        print(f"✅ Created fresh submission ID: {submission.id}")
        print(f"   Team: {team.team_name}")
        print(f"   Mission: {submission.mission}")
        print(f"   Content: {submission.selected_value[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_fresh_submission()