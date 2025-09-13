#!/usr/bin/env python
"""
Script to check and compare GameLearningModule data between local and production
"""
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from group_learning.models import GameLearningModule

def check_local_data():
    """Check GameLearningModule data in local database"""
    print("=== LOCAL DATABASE - GameLearningModule Data ===")
    
    modules = GameLearningModule.objects.all().order_by('id')
    print(f"Total GameLearningModule records: {modules.count()}")
    
    if modules.count() == 0:
        print("❌ No GameLearningModule records found in local database")
        return []
    
    local_data = []
    for module in modules:
        data = {
            'id': module.id,
            'title': module.title,
            'game_type': module.game_type,
            'trigger_condition': module.trigger_condition,
            'is_enabled': module.is_enabled,
            'view_count': module.view_count,
            'skip_count': module.skip_count,
            'created_at': module.created_at.isoformat() if module.created_at else None,
        }
        local_data.append(data)
        print(f"  ID: {module.id} | Title: {module.title[:50]}... | Game: {module.game_type} | Enabled: {module.is_enabled}")
    
    return local_data

def check_production_access():
    """Check if we can access production data via API"""
    print("\n=== PRODUCTION ACCESS CHECK ===")
    
    # Try to access the production diagnostics API
    try:
        response = requests.get(
            'https://decipherworld.com/learn/api/diagnostics/',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Production diagnostics API accessible")
            
            # Check if GameLearningModule info is in the response
            if 'model_fields' in data and 'GameLearningModule' in data['model_fields']:
                fields = data['model_fields']['GameLearningModule']
                print(f"✅ GameLearningModule model exists in production with {len(fields)} fields")
                return True
            else:
                print("⚠️ GameLearningModule model info not found in diagnostics")
                
        else:
            print(f"❌ Production API returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to access production API: {e}")
    
    return False

def create_data_export():
    """Create a JSON export of local GameLearningModule data"""
    print("\n=== CREATING DATA EXPORT ===")
    
    modules = GameLearningModule.objects.all().order_by('id')
    export_data = []
    
    for module in modules:
        # Create a comprehensive export
        data = {
            'id': module.id,
            'title': module.title,
            'game_type': module.game_type,
            'trigger_condition': module.trigger_condition,
            'is_enabled': module.is_enabled,
            'is_skippable': module.is_skippable,
            'view_count': module.view_count,
            'skip_count': module.skip_count,
            'display_timing': module.display_timing,
            'principle_explanation': module.principle_explanation,
            'key_takeaways': module.key_takeaways,
            'historical_context': module.historical_context if hasattr(module, 'historical_context') else None,
            'real_world_example': module.real_world_example if hasattr(module, 'real_world_example') else None,
            'created_at': module.created_at.isoformat() if module.created_at else None,
            'updated_at': module.updated_at.isoformat() if module.updated_at else None,
        }
        
        # Add trigger-specific fields
        if hasattr(module, 'trigger_question_id'):
            data['trigger_question_id'] = module.trigger_question_id
        if hasattr(module, 'trigger_option_id'):
            data['trigger_option_id'] = module.trigger_option_id
        if hasattr(module, 'trigger_topic'):
            data['trigger_topic'] = module.trigger_topic
        if hasattr(module, 'min_score'):
            data['min_score'] = module.min_score
        if hasattr(module, 'max_score'):
            data['max_score'] = module.max_score
            
        export_data.append(data)
    
    # Save to file
    export_file = 'gamelearningmodule_export.json'
    with open(export_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Data exported to {export_file}")
    print(f"   Total records: {len(export_data)}")
    
    return export_data

def main():
    print("🔍 Checking GameLearningModule Data Sync\n")
    
    # Check local data
    local_data = check_local_data()
    
    # Check production access
    production_accessible = check_production_access()
    
    # Create export for manual comparison
    export_data = create_data_export()
    
    print("\n=== SUMMARY ===")
    print(f"Local GameLearningModule records: {len(local_data)}")
    print(f"Production API accessible: {'Yes' if production_accessible else 'No'}")
    print(f"Data export created: gamelearningmodule_export.json")
    
    if len(local_data) == 0:
        print("\n⚠️ No local data to sync to production")
    else:
        print(f"\n📋 Next steps:")
        print("1. Review the exported data in gamelearningmodule_export.json")
        print("2. Check production database directly via SSH or admin panel")
        print("3. Run data migration/sync if needed")

if __name__ == "__main__":
    main()