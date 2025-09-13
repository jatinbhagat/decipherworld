#!/usr/bin/env python3
"""
Script to check GameLearningModule data on production.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from group_learning.models import GameLearningModule, ConstitutionQuestion


def check_production_modules():
    """Check what learning modules exist on production."""
    print("🔍 Checking Production GameLearningModule Data")
    print("=" * 50)
    
    try:
        count = GameLearningModule.objects.count()
        print(f"📊 Total Learning Modules: {count}")
        print()
        
        if count == 0:
            print("❌ No learning modules found on production!")
            print("This explains why the learning content is missing.")
            return False
            
        print("📋 Learning Modules on Production:")
        for module in GameLearningModule.objects.all():
            print(f"  • ID: {module.id} - {module.title}")
            print(f"    Game Type: {module.game_type}")
            print(f"    Trigger: {module.trigger_condition}")
            print(f"    Constitution Chapter: {module.constitution_chapter or 'None'}")
            print()
        
        # Also check questions
        q_count = ConstitutionQuestion.objects.count()
        print(f"📊 Total Constitution Questions: {q_count}")
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Error checking production data: {e}")
        return False


if __name__ == '__main__':
    print("🔧 Production Learning Module Check")
    print("=" * 50)
    
    try:
        has_modules = check_production_modules()
        
        if has_modules:
            print("✅ Production has learning modules")
        else:
            print("❌ Production is missing learning modules")
            print("   → This is why local and production don't match")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")
        sys.exit(1)