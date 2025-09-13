#!/usr/bin/env python3
"""
Production script to create Advanced Constitution Challenge game.
Run this on the production server with: python manage.py shell < create_advanced_game_production.py
"""

import os
import django
from django.db import transaction

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from group_learning.models import Game

print("🏛️ Creating Advanced Constitution Challenge Game on Production...")

try:
    with transaction.atomic():
        # Create Advanced Constitution Game
        game, created = Game.objects.get_or_create(
            title="Advanced Constitution Challenge",
            defaults={
                'subtitle': 'Advanced Governance and Constitutional Analysis (Grades 9-12)',
                'game_type': 'constitution_challenge',
                'description': 'Test your advanced understanding of constitutional principles, governance systems, and democratic institutions through complex scenarios and comparative analysis.',
                'context': 'Dive deep into advanced constitutional concepts including federalism, judicial review, electoral systems, and emergency powers. Compare Indian constitutional provisions with other major democracies.',
                'min_players': 2,
                'max_players': 8,
                'estimated_duration': 45,
                'target_age_min': 14,
                'target_age_max': 18,
                'difficulty_level': 3,  # Advanced
                'introduction_text': 'Welcome to the Advanced Constitution Challenge! You will face complex governance scenarios that test your understanding of constitutional principles, democratic institutions, and comparative government systems. Each decision will shape your nation\'s development and democratic health.',
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created Advanced Constitution Game (ID: {game.id})")
        else:
            print(f"✅ Advanced Constitution Game already exists (ID: {game.id})")
            
        print(f"🎉 Advanced Constitution Challenge ready!")
        print(f"📊 Game ID: {game.id}")
        print(f"🎯 Target: Grades 9-12 (Advanced)")
        print(f"📚 Next step: Update questions via API")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    raise e