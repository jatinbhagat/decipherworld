"""
Django management command to set up production data safely
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from group_learning.models import Game, ConstitutionQuestion, ConstitutionOption, GameLearningModule

class Command(BaseCommand):
    help = 'Set up production data for Constitution Challenge'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Setting up production data...")
        
        # Create superuser if needed
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', 
                email='admin@decipherworld.com', 
                password='DecipherWorld2025!'
            )
            self.stdout.write(self.style.SUCCESS("✅ Superuser created: admin"))
        
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
            self.stdout.write(self.style.SUCCESS(f"✅ Created game: {game.name}"))
        else:
            self.stdout.write(f"📋 Game already exists: {game.name}")
        
        # Run the existing comprehensive command to create questions
        from django.core.management import call_command
        try:
            call_command('create_constitution_sample_updated')
            self.stdout.write(self.style.SUCCESS("✅ Constitution questions and data created"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating questions: {e}"))
        
        # Verify setup
        question_count = ConstitutionQuestion.objects.filter(game=game).count()
        module_count = GameLearningModule.objects.filter(game=game).count()
        
        self.stdout.write(self.style.SUCCESS(f"🎯 Setup complete!"))
        self.stdout.write(f"   - Questions: {question_count}")
        self.stdout.write(f"   - Learning modules: {module_count}")
        self.stdout.write("🌐 Site ready: https://decipherworld-app.azurewebsites.net/learn/")