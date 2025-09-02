#!/usr/bin/env python
"""
Data migration script: Supabase → Azure PostgreSQL
Transfers all decipherworld data from Supabase to Azure PostgreSQL
"""

import os
import sys
import json
import django
from datetime import datetime

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.azure')
    django.setup()

def load_backup_data(backup_file):
    """Load backup data from JSON file"""
    try:
        with open(backup_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Backup file not found: {backup_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in backup file: {e}")
        return None

def migrate_data_to_azure(backup_data):
    """Migrate data from backup to Azure PostgreSQL"""
    from core.models import SchoolDemoRequest, DemoRequest, Course
    from django.db import transaction
    
    print("🚀 Starting data migration to Azure PostgreSQL...")
    print(f"📊 Source: {backup_data['source_database']}")
    print(f"⏰ Backup created: {backup_data['timestamp']}")
    
    success_count = {'school_demo': 0, 'demo': 0, 'course': 0}
    error_count = {'school_demo': 0, 'demo': 0, 'course': 0}
    
    # Migrate SchoolDemoRequest records
    print("\\n📋 Migrating School Demo Requests...")
    for record in backup_data.get('school_demo_requests', []):
        try:
            with transaction.atomic():
                # Check if record already exists (avoid duplicates)
                existing = SchoolDemoRequest.objects.filter(
                    email=record['email'],
                    school_name=record['school_name'],
                    created_at=record['created_at']
                ).first()
                
                if existing:
                    print(f"⚠️  Skipping duplicate: {record['school_name']} ({record['email']})")
                    continue
                
                # Create new record in Azure
                school_demo = SchoolDemoRequest(
                    school_name=record['school_name'],
                    contact_person=record['contact_person'],
                    email=record['email'],
                    phone=record['phone'],
                    city=record['city'],
                    student_count=record['student_count'],
                    interested_products=record['interested_products'],
                    additional_requirements=record['additional_requirements'],
                    preferred_demo_time=record['preferred_demo_time'],
                    created_at=record['created_at'],
                    is_contacted=record['is_contacted']
                )
                school_demo.save()
                success_count['school_demo'] += 1
                print(f"✅ Migrated: {record['school_name']}")
                
        except Exception as e:
            error_count['school_demo'] += 1
            print(f"❌ Error migrating school demo {record['school_name']}: {e}")
    
    # Migrate DemoRequest records
    print("\\n📞 Migrating Demo Requests...")
    for record in backup_data.get('demo_requests', []):
        try:
            with transaction.atomic():
                # Check if record already exists
                existing = DemoRequest.objects.filter(
                    email=record['email'],
                    name=record['name'],
                    created_at=record['created_at']
                ).first()
                
                if existing:
                    print(f"⚠️  Skipping duplicate: {record['name']} ({record['email']})")
                    continue
                
                # Create new record in Azure
                demo = DemoRequest(
                    name=record['name'],
                    email=record['email'],
                    school=record['school'],
                    message=record['message'],
                    created_at=record['created_at']
                )
                demo.save()
                success_count['demo'] += 1
                print(f"✅ Migrated: {record['name']} ({record['school']})")
                
        except Exception as e:
            error_count['demo'] += 1
            print(f"❌ Error migrating demo request {record['name']}: {e}")
    
    # Migrate Course records
    print("\\n📚 Migrating Courses...")
    for record in backup_data.get('courses', []):
        try:
            with transaction.atomic():
                # Check if record already exists
                existing = Course.objects.filter(
                    title=record['title'],
                    created_at=record['created_at']
                ).first()
                
                if existing:
                    print(f"⚠️  Skipping duplicate: {record['title']}")
                    continue
                
                # Create new record in Azure
                course = Course(
                    title=record['title'],
                    description=record['description'],
                    created_at=record['created_at'],
                    updated_at=record['updated_at']
                )
                course.save()
                success_count['course'] += 1
                print(f"✅ Migrated: {record['title']}")
                
        except Exception as e:
            error_count['course'] += 1
            print(f"❌ Error migrating course {record['title']}: {e}")
    
    # Migration summary
    print("\\n" + "="*60)
    print("📊 MIGRATION SUMMARY")
    print("="*60)
    print(f"✅ School Demo Requests: {success_count['school_demo']} migrated")
    print(f"✅ Demo Requests: {success_count['demo']} migrated")
    print(f"✅ Courses: {success_count['course']} migrated")
    
    total_success = sum(success_count.values())
    total_errors = sum(error_count.values())
    
    print(f"\\n🎯 Total Success: {total_success}")
    print(f"❌ Total Errors: {total_errors}")
    
    if total_errors == 0:
        print("🎉 Migration completed successfully!")
        return True
    else:
        print(f"⚠️  Migration completed with {total_errors} errors")
        return False

def verify_migration():
    """Verify data migration was successful"""
    from core.models import SchoolDemoRequest, DemoRequest, Course
    from django.db import connection
    
    print("\\n🔍 Verifying Azure PostgreSQL migration...")
    
    # Check database connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to: {version[:50]}...")
    
    # Count records in Azure
    school_count = SchoolDemoRequest.objects.count()
    demo_count = DemoRequest.objects.count()
    course_count = Course.objects.count()
    
    print(f"📊 Azure PostgreSQL Data:")
    print(f"   • School Demo Requests: {school_count}")
    print(f"   • Demo Requests: {demo_count}")
    print(f"   • Courses: {course_count}")
    
    # Test a query
    if school_count > 0:
        latest_school = SchoolDemoRequest.objects.latest('created_at')
        print(f"✅ Latest school demo: {latest_school.school_name} ({latest_school.created_at})")
    
    print("✅ Migration verification complete!")
    return True

def main():
    """Main migration function"""
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_azure.py <backup_file.json>")
        print("Example: python migrate_to_azure.py supabase_backup_20250902_073450.json")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    print("🚀 Azure Migration Script - Decipherworld")
    print("="*50)
    
    # Setup Django
    try:
        setup_django()
        print("✅ Django setup complete")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        sys.exit(1)
    
    # Load backup data
    backup_data = load_backup_data(backup_file)
    if not backup_data:
        sys.exit(1)
    
    print(f"✅ Backup data loaded from {backup_file}")
    
    # Run migrations first
    print("\\n🗄️ Running Django migrations on Azure...")
    from django.core.management import call_command
    try:
        call_command('migrate', verbosity=0)
        print("✅ Database migrations completed")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    # Migrate data
    migration_success = migrate_data_to_azure(backup_data)
    
    # Verify migration
    if migration_success:
        verify_migration()
        print("\\n🎉 Azure migration completed successfully!")
        print("🌐 Your application is ready to deploy to Azure App Service!")
    else:
        print("\\n⚠️  Migration had errors - please review and retry")
        sys.exit(1)

if __name__ == "__main__":
    main()