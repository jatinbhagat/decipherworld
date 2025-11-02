#!/usr/bin/env python3
import os, sys
sys.path.append('/Users/jatinbhagat/projects/decipherworld')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
import django
django.setup()
from group_learning.models import DesignThinkingSession

try:
    session = DesignThinkingSession.objects.get(session_code='G03KHM')
    print(f"✅ G03KHM exists: {session.design_game}")
except:
    print("❌ G03KHM not found")
    
all_sessions = DesignThinkingSession.objects.values_list('session_code', flat=True)
print(f"All sessions: {list(all_sessions)}")