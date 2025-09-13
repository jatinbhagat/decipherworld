#!/usr/bin/env python
"""
Script to check GameLearningModule data in production via API
"""
import requests
import json

def check_production_gamelearningmodule():
    """Check GameLearningModule data in production"""
    print("=== PRODUCTION DATABASE - GameLearningModule Check ===")
    
    # Use the production diagnostics API to check the data
    try:
        response = requests.get(
            'https://decipherworld.com/learn/api/diagnostics/',
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connected to production diagnostics API")
            
            # Check database info
            if 'database_info' in data:
                db_info = data['database_info']
                print(f"Database: {db_info.get('database', 'Unknown')}")
                print(f"Host: {db_info.get('host', 'Unknown')}")
            
            # Check model fields info
            if 'model_fields' in data:
                models = data['model_fields']
                
                if 'GameLearningModule' in models:
                    fields = models['GameLearningModule']
                    print(f"✅ GameLearningModule model exists with {len(fields)} fields:")
                    for field_name, field_info in fields.items():
                        print(f"  - {field_name}: {field_info.get('type', 'unknown')}")
                else:
                    print("❌ GameLearningModule model not found in production")
                    print("Available models:")
                    for model_name in models.keys():
                        print(f"  - {model_name}")
            
            # Try to get actual record counts via custom API if available
            return True
            
        else:
            print(f"❌ Production API returned status {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Failed to check production: {e}")
    
    return False

def try_production_test_api():
    """Try the production test API to get more detailed info"""
    print("\n=== TRYING PRODUCTION TEST API ===")
    
    try:
        response = requests.get(
            'https://decipherworld.com/learn/api/test/',
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Production test API accessible")
            
            # Look for GameLearningModule info
            if 'game_learning_modules' in data:
                modules = data['game_learning_modules']
                print(f"✅ Found {len(modules)} GameLearningModule records in production:")
                
                for module in modules[:5]:  # Show first 5
                    print(f"  ID: {module.get('id')} | Title: {module.get('title', '')[:50]}...")
                
                if len(modules) > 5:
                    print(f"  ... and {len(modules) - 5} more")
                
                return modules
            else:
                print("⚠️ No GameLearningModule data found in test API response")
                print("Available keys in response:")
                for key in data.keys():
                    print(f"  - {key}")
            
        else:
            print(f"❌ Test API returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to access test API: {e}")
    
    return None

def compare_with_local_export():
    """Compare with local export data"""
    print("\n=== COMPARING WITH LOCAL DATA ===")
    
    try:
        with open('gamelearningmodule_export.json', 'r') as f:
            local_data = json.load(f)
        
        print(f"Local data: {len(local_data)} records")
        
        # Show local records for comparison
        print("\nLocal GameLearningModule records:")
        for module in local_data:
            enabled = "✅" if module.get('is_enabled') else "❌"
            print(f"  {enabled} ID: {module.get('id')} | {module.get('title', '')[:50]}...")
        
        return local_data
        
    except FileNotFoundError:
        print("❌ Local export file not found. Run check_gamelearningmodule_data.py first")
        return None

def main():
    print("🔍 Checking Production GameLearningModule Data\n")
    
    # Check production diagnostics
    diagnostics_ok = check_production_gamelearningmodule()
    
    # Try test API for actual data
    production_data = try_production_test_api()
    
    # Compare with local
    local_data = compare_with_local_export()
    
    print("\n=== COMPARISON SUMMARY ===")
    
    if local_data:
        enabled_local = len([m for m in local_data if m.get('is_enabled')])
        print(f"Local records: {len(local_data)} total, {enabled_local} enabled")
    
    if production_data:
        enabled_prod = len([m for m in production_data if m.get('is_enabled')])
        print(f"Production records: {len(production_data)} total, {enabled_prod} enabled")
        
        if local_data:
            if len(local_data) == len(production_data):
                print("✅ Record counts match")
            else:
                print(f"⚠️ Record count mismatch: {len(local_data)} local vs {len(production_data)} production")
    else:
        print("❌ Could not retrieve production data for comparison")
        print("💡 Suggestion: SSH into production to check manually or create data sync script")

if __name__ == "__main__":
    main()