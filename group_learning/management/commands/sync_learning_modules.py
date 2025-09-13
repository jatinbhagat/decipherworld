from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction
from group_learning.models import GameLearningModule, ConstitutionQuestion, ConstitutionOption
import json


class Command(BaseCommand):
    help = 'Sync learning modules from local to production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export current data to JSON file',
        )
        parser.add_argument(
            '--import',
            action='store_true',
            help='Import data from JSON file',
        )
        parser.add_argument(
            '--file',
            type=str,
            default='gamelearningmodule_sync.json',
            help='JSON file name for import/export',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing learning modules before import',
        )

    def handle(self, *args, **options):
        if options['export']:
            self.export_data(options['file'])
        elif options['import']:
            self.import_data(options['file'], options['clear'])
        else:
            self.show_current_state()

    def show_current_state(self):
        """Show current learning module state"""
        self.stdout.write("🔍 Current GameLearningModule State")
        self.stdout.write("=" * 50)
        
        count = GameLearningModule.objects.count()
        q_count = ConstitutionQuestion.objects.count()
        o_count = ConstitutionOption.objects.count()
        
        self.stdout.write(f"📊 Learning Modules: {count}")
        self.stdout.write(f"📊 Constitution Questions: {q_count}")
        self.stdout.write(f"📊 Constitution Options: {o_count}")
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING("❌ No learning modules found!")
            )
        else:
            self.stdout.write("📋 Learning Modules:")
            for module in GameLearningModule.objects.all():
                self.stdout.write(f"  • ID: {module.id} - {module.title}")
        
        self.stdout.write("\n💡 Usage:")
        self.stdout.write("  --export: Export current data")
        self.stdout.write("  --import: Import data from file")
        self.stdout.write("  --clear: Clear existing data before import")

    def export_data(self, filename):
        """Export learning modules to JSON"""
        self.stdout.write(f"📤 Exporting learning modules to {filename}...")
        
        try:
            # Export all related models
            modules = GameLearningModule.objects.all()
            questions = ConstitutionQuestion.objects.all()
            options = ConstitutionOption.objects.all()
            
            data = {
                'learning_modules': json.loads(serializers.serialize('json', modules)),
                'constitution_questions': json.loads(serializers.serialize('json', questions)),
                'constitution_options': json.loads(serializers.serialize('json', options)),
                'counts': {
                    'modules': modules.count(),
                    'questions': questions.count(),
                    'options': options.count(),
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Exported {data['counts']['modules']} modules, {data['counts']['questions']} questions, {data['counts']['options']} options")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Export failed: {e}")
            )

    def import_data(self, filename, clear_existing):
        """Import learning modules from JSON"""
        self.stdout.write(f"📥 Importing learning modules from {filename}...")
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            with transaction.atomic():
                if clear_existing:
                    self.stdout.write("🗑️ Clearing existing data...")
                    GameLearningModule.objects.all().delete()
                    ConstitutionQuestion.objects.all().delete()
                    ConstitutionOption.objects.all().delete()
                
                # Import in correct order (questions first, then options, then modules)
                
                # 1. Import questions
                if 'constitution_questions' in data:
                    self.stdout.write("📝 Importing constitution questions...")
                    for item in data['constitution_questions']:
                        # Remove primary key to allow auto-assignment
                        fields = item['fields']
                        if 'game' in fields and fields['game']:
                            # Skip if references a game that might not exist
                            fields['game'] = None
                        ConstitutionQuestion.objects.create(**fields)
                
                # 2. Import options
                if 'constitution_options' in data:
                    self.stdout.write("📝 Importing constitution options...")
                    for item in data['constitution_options']:
                        fields = item['fields']
                        # Map question ID
                        if 'question' in fields:
                            try:
                                question = ConstitutionQuestion.objects.get(id=fields['question'])
                                fields['question'] = question
                            except ConstitutionQuestion.DoesNotExist:
                                self.stdout.write(f"⚠️ Skipping option - question {fields['question']} not found")
                                continue
                        ConstitutionOption.objects.create(**fields)
                
                # 3. Import learning modules
                if 'learning_modules' in data:
                    self.stdout.write("📚 Importing learning modules...")
                    for item in data['learning_modules']:
                        fields = item['fields']
                        
                        # Handle foreign key relationships
                        if 'trigger_question' in fields and fields['trigger_question']:
                            try:
                                question = ConstitutionQuestion.objects.get(id=fields['trigger_question'])
                                fields['trigger_question'] = question
                            except ConstitutionQuestion.DoesNotExist:
                                fields['trigger_question'] = None
                        
                        if 'trigger_option' in fields and fields['trigger_option']:
                            try:
                                option = ConstitutionOption.objects.get(id=fields['trigger_option'])
                                fields['trigger_option'] = option
                            except ConstitutionOption.DoesNotExist:
                                fields['trigger_option'] = None
                        
                        GameLearningModule.objects.create(**fields)
            
            # Show results
            final_count = GameLearningModule.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Import completed! {final_count} learning modules now available.")
            )
            
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"❌ File {filename} not found!")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Import failed: {e}")
            )