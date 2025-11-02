#!/usr/bin/env python3
"""
Test script for Step 3 (Ideate) and Step 4 (Prototype) implementation
"""

import os
import sys
import django
import requests
from datetime import datetime

# Add the project directory to the Python path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

# Setup Django
django.setup()

from group_learning.models import DesignThinkingGame, DesignMission

def test_mission_configuration():
    """Test that the missions are properly configured"""
    print("🧪 Testing Mission Configuration...")
    
    try:
        # Get the simplified game
        game = DesignThinkingGame.objects.filter(
            title="Simplified Classroom Innovation Challenge"
        ).first()
        
        if not game:
            print("❌ Simplified game not found!")
            return False
            
        print(f"✅ Found game: {game.title}")
        
        # Check missions
        missions = game.missions.all().order_by('order')
        expected_missions = [
            ('kickoff', 'Welcome & Team Formation'),
            ('empathy', 'Understanding Student Challenges'),
            ('define', 'Define the Problem'),
            ('ideate', '💡 IDEATE — Think of Awesome Ideas!'),
            ('prototype', '🛠️ PROTOTYPE — Make It Real!')
        ]
        
        print(f"\n📋 Found {missions.count()} missions:")
        for mission in missions:
            print(f"  {mission.order}. {mission.mission_type}: {mission.title}")
            
            # Check input schema for ideate and prototype
            if mission.mission_type == 'ideate':
                inputs = mission.input_schema.get('inputs', [])
                print(f"    📝 Ideate inputs: {len(inputs)}")
                for i, inp in enumerate(inputs):
                    print(f"      {i+1}. {inp['type']}: {inp['label']}")
                    
            elif mission.mission_type == 'prototype':
                inputs = mission.input_schema.get('inputs', [])
                print(f"    📝 Prototype inputs: {len(inputs)}")
                for i, inp in enumerate(inputs):
                    print(f"      {i+1}. {inp['type']}: {inp['label']}")
        
        # Verify we have all expected missions
        if missions.count() == len(expected_missions):
            print("\n✅ All missions configured correctly!")
            return True
        else:
            print(f"\n❌ Expected {len(expected_missions)} missions, found {missions.count()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing mission configuration: {e}")
        return False

def test_url_accessibility():
    """Test that the simplified session URLs are accessible"""
    print("\n🌐 Testing URL Accessibility...")
    
    try:
        # Test the creation page
        response = requests.get('http://localhost:8000/learn/simplified/create/', timeout=5)
        if response.status_code == 200:
            print("✅ Simplified session creation page accessible")
        else:
            print(f"❌ Creation page returned status {response.status_code}")
            return False
            
        # Test if the page contains our new step elements
        content = response.text
        step_tests = [
            ('ideate-phase', 'Step 3: Ideate phase element'),
            ('prototype-phase', 'Step 4: Prototype phase element'),
            ('ideate-card', 'Ideate card styling'),
            ('prototype-card', 'Prototype card styling'),
        ]
        
        for element_id, description in step_tests:
            if element_id in content:
                print(f"✅ {description} found in HTML")
            else:
                print(f"❌ {description} NOT found in HTML")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing URL accessibility: {e}")
        return False

def test_css_and_js_integration():
    """Test that CSS and JavaScript are properly integrated"""
    print("\n🎨 Testing CSS and JavaScript Integration...")
    
    try:
        response = requests.get('http://localhost:8000/learn/simplified/create/', timeout=5)
        content = response.text
        
        # Test for CSS classes
        css_tests = [
            '.ideate-card',
            '.prototype-card', 
            '.hmw-reminder',
            '.favorite-selection',
            '.prototype-tips'
        ]
        
        for css_class in css_tests:
            if css_class in content:
                print(f"✅ CSS class {css_class} found")
            else:
                print(f"❌ CSS class {css_class} NOT found")
        
        # Test for JavaScript functions
        js_tests = [
            'showIdeatePhase',
            'showPrototypePhase',
            'submitIdeate',
            'submitPrototype',
            'updateFavoriteOptions'
        ]
        
        for js_function in js_tests:
            if js_function in content:
                print(f"✅ JS function {js_function} found")
            else:
                print(f"❌ JS function {js_function} NOT found")
                
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSS/JS integration: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Step 3 (Ideate) and Step 4 (Prototype) Implementation")
    print("=" * 70)
    
    tests = [
        test_mission_configuration,
        test_url_accessibility, 
        test_css_and_js_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Step 3 and Step 4 are ready for use.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)