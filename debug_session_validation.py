#!/usr/bin/env python3
"""
Debug session validation issue
"""

import os
import sys

# Add Django project to path
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')

import django
django.setup()

from group_learning.models import DesignThinkingSession, DesignThinkingGame

def debug_sessions():
    print("🔍 Debugging session validation issue")
    print("="*50)
    
    # Check existing sessions
    sessions = DesignThinkingSession.objects.all().order_by('-created_at')[:5]
    print(f"📊 Found {sessions.count()} total sessions")
    
    for session in sessions:
        print(f"\n📋 Session: {session.session_code}")
        print(f"   Status: {session.status}")
        print(f"   Game: {session.game}")
        print(f"   Design Game: {session.design_game}")
        if session.design_game:
            print(f"   Design Game Title: {session.design_game.title}")
            print(f"   Auto Advance: {session.design_game.auto_advance_enabled}")
    
    print(f"\n🎮 Available Design Thinking Games:")
    games = DesignThinkingGame.objects.all()
    for game in games:
        print(f"   - {game.title} (auto_advance: {game.auto_advance_enabled})")
    
    # Check what the join validation is looking for
    print(f"\n🔍 Checking validation logic:")
    simplified_game = DesignThinkingGame.objects.filter(auto_advance_enabled=True).first()
    if simplified_game:
        print(f"✅ Found simplified game: {simplified_game.title}")
        
        # Check which sessions match this game
        matching_sessions = DesignThinkingSession.objects.filter(design_game=simplified_game)
        print(f"✅ Sessions with this game: {[s.session_code for s in matching_sessions]}")
    else:
        print("❌ No simplified game found with auto_advance_enabled=True")

if __name__ == "__main__":
    debug_sessions()