#!/usr/bin/env python
"""
Production setup script for DecipherWorld
Runs database migrations and creates sample data for Constitution Challenge
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from group_learning.models import Game, ConstitutionQuestion, ConstitutionOption, GameLearningModule

def setup_database():
    """Run migrations and create sample data"""
    print("🗄️ Running database migrations...")
    call_command('migrate', verbosity=1, interactive=False)
    
    print("👤 Creating superuser if needed...")
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin', 
            email='admin@decipherworld.com', 
            password='DecipherWorld2025!'
        )
        print("✅ Superuser created: admin / DecipherWorld2025!")
    
    print("🏛️ Setting up Constitution Challenge game...")
    
    # Create or get the game
    game, created = Game.objects.get_or_create(
        name="Build Your Country: The Constitution Challenge",
        defaults={
            'description': 'Learn Indian Constitution by building your virtual country',
            'target_audience': 'Students aged 14-18',
            'duration_minutes': 45,
            'max_players': 6,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created game: {game.name}")
    
    # Create sample questions
    if not ConstitutionQuestion.objects.filter(game=game).exists():
        print("📝 Creating sample Constitution questions...")
        
        # Question 1
        q1 = ConstitutionQuestion.objects.create(
            game=game,
            question_text="What is the fundamental principle of democracy in the Indian Constitution?",
            order=1
        )
        
        ConstitutionOption.objects.bulk_create([
            ConstitutionOption(question=q1, option_text="Military rule", letter='A', governance_impact={'democracy': -2, 'stability': +1}, is_correct=False),
            ConstitutionOption(question=q1, option_text="Rule by the people", letter='B', governance_impact={'democracy': +3, 'fairness': +2}, is_correct=True),
            ConstitutionOption(question=q1, option_text="Rule by the wealthy", letter='C', governance_impact={'democracy': -1, 'fairness': -2}, is_correct=False),
            ConstitutionOption(question=q1, option_text="Rule by one person", letter='D', governance_impact={'democracy': -3, 'freedom': -2}, is_correct=False),
        ])
        
        # Question 2
        q2 = ConstitutionQuestion.objects.create(
            game=game,
            question_text="Which fundamental right ensures freedom of speech and expression?",
            order=2
        )
        
        ConstitutionOption.objects.bulk_create([
            ConstitutionOption(question=q2, option_text="Right to Equality", letter='A', governance_impact={'fairness': +1}, is_correct=False),
            ConstitutionOption(question=q2, option_text="Right to Freedom", letter='B', governance_impact={'freedom': +3, 'democracy': +1}, is_correct=True),
            ConstitutionOption(question=q2, option_text="Right to Life", letter='C', governance_impact={'stability': +1}, is_correct=False),
            ConstitutionOption(question=q2, option_text="Right to Education", letter='D', governance_impact={'fairness': +1}, is_correct=False),
        ])
        
        # Question 3
        q3 = ConstitutionQuestion.objects.create(
            game=game,
            question_text="What is the purpose of the separation of powers in government?",
            order=3
        )
        
        ConstitutionOption.objects.bulk_create([
            ConstitutionOption(question=q3, option_text="To create confusion", letter='A', governance_impact={'stability': -2}, is_correct=False),
            ConstitutionOption(question=q3, option_text="To prevent abuse of power", letter='B', governance_impact={'democracy': +2, 'fairness': +2, 'stability': +1}, is_correct=True),
            ConstitutionOption(question=q3, option_text="To slow down decisions", letter='C', governance_impact={'stability': -1}, is_correct=False),
            ConstitutionOption(question=q3, option_text="To reduce efficiency", letter='D', governance_impact={'stability': -1}, is_correct=False),
        ])
        
        print(f"✅ Created {ConstitutionQuestion.objects.filter(game=game).count()} Constitution questions")
        
        # Create learning modules
        if not GameLearningModule.objects.filter(game=game).exists():
            print("📚 Creating learning modules...")
            
            GameLearningModule.objects.bulk_create([
                GameLearningModule(
                    game=game,
                    title="Understanding Democracy",
                    explanation="Democracy means 'rule by the people.' In India, we practice representative democracy where citizens elect their representatives.",
                    key_concept="Popular Sovereignty",
                    historical_context="The Indian Constitution adopted democratic principles from global experiences while maintaining our unique cultural context.",
                    real_world_examples="Elections, voting rights, citizen participation in governance",
                    impact_description="Your choice strengthens democratic institutions and citizen participation in your virtual nation.",
                    question_order=1,
                    is_active=True
                ),
                GameLearningModule(
                    game=game,
                    title="Fundamental Rights",
                    explanation="Fundamental rights are basic human rights guaranteed by the Constitution to ensure dignity and freedom for all citizens.",
                    key_concept="Constitutional Rights",
                    historical_context="These rights were inspired by global human rights movements and adapted for Indian society.",
                    real_world_examples="Freedom of speech, right to equality, right to life and liberty",
                    impact_description="Protecting fundamental rights creates a more free and just society in your nation.",
                    question_order=2,
                    is_active=True
                ),
                GameLearningModule(
                    game=game,
                    title="Separation of Powers",
                    explanation="The Constitution divides government power among Legislature (makes laws), Executive (implements laws), and Judiciary (interprets laws).",
                    key_concept="Checks and Balances",
                    historical_context="This system prevents concentration of power and protects against tyranny, inspired by Montesquieu's philosophy.",
                    real_world_examples="Parliament makes laws, PM implements them, Supreme Court reviews them",
                    impact_description="Proper separation of powers ensures balanced governance and prevents abuse of authority in your nation.",
                    question_order=3,
                    is_active=True
                ),
            ])
            
            print(f"✅ Created {GameLearningModule.objects.filter(game=game).count()} learning modules")
    
    print("🎯 Constitution Challenge setup complete!")
    print(f"📊 Total questions: {ConstitutionQuestion.objects.filter(game=game).count()}")
    print(f"📚 Total learning modules: {GameLearningModule.objects.filter(game=game).count()}")
    
    print("\n🌐 Production site ready:")
    print("   - Homepage: https://decipherworld-app.azurewebsites.net/")
    print("   - Group Learning: https://decipherworld-app.azurewebsites.net/learn/")
    print("   - Admin: https://decipherworld-app.azurewebsites.net/admin/")
    print(f"   - Admin login: admin / DecipherWorld2025!")

if __name__ == '__main__':
    setup_database()