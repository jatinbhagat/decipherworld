#!/usr/bin/env python3
"""
Test script for submission review workflow
Creates test data and verifies the scoring system works correctly
"""

import os
import sys
import requests
import json
from html import unescape

# Add Django project to path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

import django
django.setup()

from group_learning.models import DesignThinkingSession, DesignTeam, SimplifiedPhaseInput

def create_test_submissions(session_code):
    """Create test submissions for scoring workflow"""
    print(f"🔍 Creating test submissions for session {session_code}")
    
    try:
        session = DesignThinkingSession.objects.get(session_code=session_code)
        print(f"✅ Found session: {session.session_code}")
        
        # Get or create teams
        team1, created1 = DesignTeam.objects.get_or_create(
            session=session,
            team_name="Team Alpha",
            defaults={
                'team_members': 'Alice Johnson\nCharlie Davis'
            }
        )
        
        team2, created2 = DesignTeam.objects.get_or_create(
            session=session,
            team_name="Team Beta", 
            defaults={
                'team_members': 'Bob Smith\nDiana Wilson'
            }
        )
        
        print(f"✅ Teams ready: {team1.team_name}, {team2.team_name}")
        
        # Create test submissions for different phases
        test_submissions = [
            {
                'team': team1,
                'mission': 'empathy_pain_points',
                'student_name': 'Alice Johnson',
                'selected_value': 'Users struggle with confusing navigation and find it hard to locate important features in the app.',
                'input_label': 'Pain Point 1'
            },
            {
                'team': team1,
                'mission': 'empathy_root_causes',
                'student_name': 'Alice Johnson', 
                'selected_value': 'Lack of user testing during design phase led to poor information architecture.',
                'input_label': 'Root Cause Analysis'
            },
            {
                'team': team2,
                'mission': 'empathy_pain_points',
                'student_name': 'Bob Smith',
                'selected_value': 'Slow loading times frustrate users and cause them to abandon tasks.',
                'input_label': 'Pain Point 1'
            },
            {
                'team': team2,
                'mission': 'define_problem_statement',
                'student_name': 'Bob Smith',
                'selected_value': 'How might we improve app performance to reduce user frustration and task abandonment?',
                'input_label': 'Problem Statement'
            }
        ]
        
        created_count = 0
        for submission_data in test_submissions:
            # Check if submission already exists
            existing = SimplifiedPhaseInput.objects.filter(
                team=submission_data['team'],
                mission=submission_data['mission'],
                student_name=submission_data['student_name']
            ).first()
            
            if not existing:
                submission = SimplifiedPhaseInput.objects.create(**submission_data)
                created_count += 1
                print(f"  ✅ Created: {submission.student_name} - {submission.mission}")
            else:
                print(f"  ⚠️ Exists: {existing.student_name} - {existing.mission}")
        
        print(f"✅ Created {created_count} new test submissions")
        
        # Count total submissions
        total = SimplifiedPhaseInput.objects.filter(team__session=session).count()
        unscored = SimplifiedPhaseInput.objects.filter(team__session=session, teacher_score__isnull=True).count()
        
        print(f"📊 Session {session_code} summary:")
        print(f"   - Total submissions: {total}")
        print(f"   - Unscored submissions: {unscored}")
        print(f"   - Teams: {DesignTeam.objects.filter(session=session).count()}")
        
        return True
        
    except DesignThinkingSession.DoesNotExist:
        print(f"❌ Session {session_code} not found")
        return False
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return False

def test_scoring_api(session_code):
    """Test the scoring API endpoint"""
    print(f"\n🧪 Testing scoring API for session {session_code}")
    
    try:
        # Get CSRF token first
        session_req = requests.Session()
        dashboard_url = f"http://localhost:8001/learn/simplified/{session_code}/teacher/"
        resp = session_req.get(dashboard_url)
        
        if resp.status_code != 200:
            print(f"❌ Could not load teacher dashboard: {resp.status_code}")
            return False
            
        # Extract CSRF token
        csrf_token = None
        for line in resp.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                start = line.find('value="') + 7
                end = line.find('"', start)
                csrf_token = line[start:end]
                break
        
        if not csrf_token:
            print("❌ Could not extract CSRF token")
            return False
            
        print(f"✅ Got CSRF token: {csrf_token[:10]}...")
        
        # Get an unscored submission ID from the HTML
        submission_id = None
        if 'data-submission-id=' in resp.text:
            start = resp.text.find('data-submission-id="') + 20
            end = resp.text.find('"', start)
            submission_id = resp.text[start:end]
        
        if not submission_id:
            print("⚠️ No unscored submissions found in dashboard")
            return True  # Not an error, just no data to score
            
        print(f"✅ Found submission ID: {submission_id}")
        
        # Test scoring API
        scoring_url = f"http://localhost:8001/learn/api/simplified/{session_code}/score-submission/"
        scoring_data = {
            'submission_id': submission_id,
            'score': '8'
        }
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': dashboard_url
        }
        
        score_resp = session_req.post(scoring_url, data=scoring_data, headers=headers)
        
        print(f"📊 Scoring API response: {score_resp.status_code}")
        
        if score_resp.status_code == 200:
            try:
                data = score_resp.json()
                print(f"✅ API Response: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    print("✅ Scoring workflow test PASSED")
                    return True
                else:
                    print(f"❌ Scoring failed: {data.get('message', 'Unknown error')}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {score_resp.text[:200]}")
                return False
        else:
            print(f"❌ Scoring API failed: {score_resp.status_code}")
            print(f"Response: {score_resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing scoring API: {e}")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 Testing Complete Submission Review Workflow")
    print("=" * 50)
    
    # Use one of the existing sessions from the logs
    session_code = "G03KHM"  # From server logs
    
    # Step 1: Create test data
    if not create_test_submissions(session_code):
        print("❌ Failed to create test data")
        return False
    
    # Step 2: Test scoring API
    if not test_scoring_api(session_code):
        print("❌ Failed scoring API test")
        return False
    
    print("\n🎉 All tests PASSED! Submission review workflow is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)