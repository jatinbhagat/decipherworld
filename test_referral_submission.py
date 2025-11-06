#!/usr/bin/env python
"""Test script for school referral form submission"""

import requests
import json
from bs4 import BeautifulSoup

def test_referral_submission():
    """Test submitting a school referral form"""
    
    # URL for the referral form
    form_url = 'http://127.0.0.1:8000/school-referral/'
    
    # First, get the form to extract CSRF token
    session = requests.Session()
    print("📋 Getting referral form...")
    
    try:
        response = session.get(form_url)
        response.raise_for_status()
        
        # Parse HTML to get CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        print(f"✅ Form loaded successfully, CSRF token: {csrf_token[:8]}...")
        
        # Test data for form submission
        test_data = {
            'csrfmiddlewaretoken': csrf_token,
            'referrer_name': 'Test Referrer Updated',
            'referrer_email': 'test.updated@example.com',
            'referrer_phone': '+91 9876543210',
            'referrer_relationship': 'Teacher at different school',
            'school_name': 'XYZ High School',
            'school_address': '456 Learning Avenue, Education City',
            'school_city': 'Delhi',
            'school_state': 'Delhi',
            'school_pincode': '110001',
            'contact_person_name': 'Dr. Patel',
            'contact_person_designation': 'Principal',
            'contact_person_email': 'principal@xyzschool.edu',
            'contact_person_phone': '+91 9876543211',
            'school_board': 'icse',
            'current_education_programs': 'Traditional curriculum with some digital tools',
            'interest_level': 'high',
            'additional_notes': 'The school is looking to modernize their teaching methods with AI integration.'
        }
        
        # Submit the form
        print("\n📤 Submitting referral form...")
        submit_response = session.post(form_url, data=test_data)
        
        # Check if submission was successful (either redirect 302 or success page 200)
        if submit_response.status_code == 302:
            print("✅ Form submitted successfully! Redirected to:", submit_response.headers.get('Location'))
            
            # Follow the redirect to see the success page
            success_url = submit_response.headers.get('Location')
            if success_url:
                success_response = session.get(f"http://127.0.0.1:8000{success_url}")
                if success_response.status_code == 200:
                    print("✅ Success page loaded correctly")
                    print(f"📊 Success page size: {len(success_response.text)} bytes")
                    
                    # Verify the referral was saved to database
                    import subprocess
                    result = subprocess.run([
                        'python', 'manage.py', 'shell', '-c',
                        'from core.models import SchoolReferral; print("Database count:", SchoolReferral.objects.count())'
                    ], capture_output=True, text=True)
                    print("📊", result.stdout.strip())
                else:
                    print(f"❌ Error loading success page: {success_response.status_code}")
        elif submit_response.status_code == 200 and "Referral Submitted Successfully" in submit_response.text:
            print("✅ Form submitted successfully! Success page loaded directly.")
            print(f"📊 Success page size: {len(submit_response.text)} bytes")
            
            # Verify the referral was saved to database
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                'from core.models import SchoolReferral; print("Database count:", SchoolReferral.objects.count())'
            ], capture_output=True, text=True)
            print("📊", result.stdout.strip())
        else:
            print(f"❌ Form submission failed: {submit_response.status_code}")
            # Look for form errors in the response
            error_soup = BeautifulSoup(submit_response.text, 'html.parser')
            error_elements = error_soup.find_all(class_=['alert-error', 'text-red-500', 'error'])
            if error_elements:
                print("🚨 Found form errors:")
                for error in error_elements:
                    print(f"  - {error.get_text().strip()}")
            else:
                print("📄 Response preview:", submit_response.text[:500])
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        
    print("\n🎯 Test completed!")

if __name__ == '__main__':
    test_referral_submission()