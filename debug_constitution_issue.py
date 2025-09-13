#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from group_learning.models import GameSession, ConstitutionTeam

def debug_constitution_issue():
    print("=== Debugging Constitution Challenge Issue ===")
    
    # Check if session U5CSGI exists
    try:
        session = GameSession.objects.get(session_code='U5CSGI')
        print(f"✓ Session U5CSGI found: {session}")
        print(f"  Game: {session.game}")
        print(f"  Game Type: {session.game.game_type}")
    except GameSession.DoesNotExist:
        print("✗ Session U5CSGI not found")
        return
    
    # Check teams in this session
    teams = ConstitutionTeam.objects.filter(session=session)
    print(f"\nTeams in session U5CSGI: {teams.count()}")
    
    for team in teams:
        print(f"  Team ID: {team.id}, Name: {team.team_name}")
    
    # Check if team_id=8 exists
    try:
        team_8 = ConstitutionTeam.objects.get(id=8, session=session)
        print(f"\n✓ Team ID 8 found: {team_8.team_name}")
    except ConstitutionTeam.DoesNotExist:
        print("\n✗ Team ID 8 not found in this session")
        
        # Check if team_id=8 exists in any session
        try:
            team_8_any = ConstitutionTeam.objects.get(id=8)
            print(f"  But team ID 8 exists in session: {team_8_any.session.session_code}")
        except ConstitutionTeam.DoesNotExist:
            print("  Team ID 8 does not exist at all")

if __name__ == "__main__":
    debug_constitution_issue()