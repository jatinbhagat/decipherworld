#!/usr/bin/env python
"""
Script to create a data sync command for GameLearningModule to production
This will generate the Django management commands needed to sync data
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from group_learning.models import GameLearningModule

def create_sync_script():
    """Create a Django management command to sync GameLearningModule data"""
    
    print("=== CREATING PRODUCTION SYNC SCRIPT ===")
    
    modules = GameLearningModule.objects.all().order_by('id')
    
    if modules.count() == 0:
        print("❌ No GameLearningModule data to sync")
        return
    
    # Create Python script that can be run in production
    script_content = '''#!/usr/bin/env python
"""
Production data sync script for GameLearningModule
Run this in production Django shell: python manage.py shell < sync_gamelearningmodule_production.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
django.setup()

from group_learning.models import GameLearningModule, ConstitutionQuestion, ConstitutionOption

def sync_gamelearningmodule_data():
    """Sync GameLearningModule data to production"""
    
    print("=== SYNCING GameLearningModule DATA TO PRODUCTION ===")
    
    # Data to create
    modules_data = [
'''
    
    # Add each module as a Python dict
    for module in modules:
        # Build the module data dict
        module_data = {
            'title': module.title,
            'game_type': module.game_type,
            'trigger_condition': module.trigger_condition,
            'is_enabled': module.is_enabled,
            'is_skippable': module.is_skippable,
            'display_timing': module.display_timing,
            'principle_explanation': module.principle_explanation,
            'key_takeaways': module.key_takeaways,
        }
        
        # Add optional fields if they exist
        optional_fields = [
            'historical_context', 'real_world_example', 'action_impact_title',
            'governance_impact', 'score_reasoning', 'country_state_changes',
            'societal_impact', 'constitution_topic_title', 'constitution_chapter',
            'constitution_principle', 'constitution_explanation', 
            'constitution_article_reference', 'historical_constitutional_context',
            'trigger_topic', 'min_score', 'max_score'
        ]
        
        for field in optional_fields:
            if hasattr(module, field):
                value = getattr(module, field)
                if value:
                    module_data[field] = value
        
        # Handle foreign key references
        if hasattr(module, 'trigger_question_id') and module.trigger_question_id:
            module_data['trigger_question_id'] = module.trigger_question_id
        if hasattr(module, 'trigger_option_id') and module.trigger_option_id:
            module_data['trigger_option_id'] = module.trigger_option_id
        
        script_content += f"        {repr(module_data)},\n"
    
    script_content += '''    ]
    
    synced_count = 0
    updated_count = 0
    
    for module_data in modules_data:
        title = module_data['title']
        
        # Check if module already exists
        existing_module = GameLearningModule.objects.filter(title=title).first()
        
        if existing_module:
            # Update existing module
            for field, value in module_data.items():
                if field not in ['trigger_question_id', 'trigger_option_id']:
                    setattr(existing_module, field, value)
            
            # Handle foreign key fields
            if 'trigger_question_id' in module_data:
                try:
                    existing_module.trigger_question_id = module_data['trigger_question_id']
                except:
                    pass  # Ignore if question doesn't exist
            
            if 'trigger_option_id' in module_data:
                try:
                    existing_module.trigger_option_id = module_data['trigger_option_id']
                except:
                    pass  # Ignore if option doesn't exist
            
            existing_module.save()
            updated_count += 1
            print(f"✅ Updated: {title[:50]}...")
            
        else:
            # Create new module
            try:
                # Remove foreign key fields for initial creation
                create_data = {k: v for k, v in module_data.items() 
                              if k not in ['trigger_question_id', 'trigger_option_id']}
                
                new_module = GameLearningModule.objects.create(**create_data)
                
                # Set foreign key fields if they exist
                if 'trigger_question_id' in module_data:
                    try:
                        new_module.trigger_question_id = module_data['trigger_question_id']
                        new_module.save()
                    except:
                        pass
                
                if 'trigger_option_id' in module_data:
                    try:
                        new_module.trigger_option_id = module_data['trigger_option_id']
                        new_module.save()
                    except:
                        pass
                
                synced_count += 1
                print(f"✅ Created: {title[:50]}...")
                
            except Exception as e:
                print(f"❌ Failed to create {title[:30]}...: {e}")
    
    print(f"\\n=== SYNC COMPLETE ===")
    print(f"Created: {synced_count} modules")
    print(f"Updated: {updated_count} modules")
    print(f"Total in production: {GameLearningModule.objects.count()}")

if __name__ == "__main__":
    sync_gamelearningmodule_data()
'''
    
    # Write the sync script
    with open('sync_gamelearningmodule_production.py', 'w') as f:
        f.write(script_content)
    
    print("✅ Sync script created: sync_gamelearningmodule_production.py")
    print(f"📊 Will sync {modules.count()} GameLearningModule records")
    
    # Show enabled modules that will be synced
    enabled_modules = modules.filter(is_enabled=True)
    print(f"📈 {enabled_modules.count()} enabled modules:")
    for module in enabled_modules:
        print(f"  ✅ {module.title[:60]}...")
    
    print(f"\n📋 To sync to production:")
    print("1. Copy sync_gamelearningmodule_production.py to production server")
    print("2. Run: python manage.py shell < sync_gamelearningmodule_production.py")
    print("3. Or run migrations if the model doesn't exist yet")

def check_missing_migrations():
    """Check if there are any missing migrations for GameLearningModule"""
    print("\n=== CHECKING FOR MISSING MIGRATIONS ===")
    
    # Check the latest migration file
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM django_migrations WHERE app='group_learning' ORDER BY id DESC LIMIT 5")
            recent_migrations = cursor.fetchall()
            
        print("Recent migrations in local database:")
        for migration in recent_migrations:
            print(f"  - {migration[0]}")
            
    except Exception as e:
        print(f"Could not check migrations: {e}")

if __name__ == "__main__":
    create_sync_script()
    check_missing_migrations()