#!/usr/bin/env python3
"""
Script to manually fix the missing governance_impact column on production.
This script can be run directly on the production server to add the missing columns.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment - use base settings locally, production when deployed
if 'DATABASE_URL' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from django.db import connection, transaction
from django.core.management.base import BaseCommand


def check_column_exists(table_name, column_name):
    """Check if a column exists in the table."""
    with connection.cursor() as cursor:
        if connection.vendor == 'postgresql':
            # PostgreSQL
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, [table_name, column_name])
        else:
            # SQLite
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return any(col[1] == column_name for col in columns)
        return cursor.fetchone() is not None


def add_missing_columns():
    """Add missing columns to the ConstitutionOption table."""
    table_name = 'group_learning_constitutionoption'
    columns_to_add = [
        ('governance_impact', 'TEXT DEFAULT \'\''),
        ('country_state_changes', 'TEXT DEFAULT \'\''),
        ('score_reasoning', 'TEXT DEFAULT \'\''),
        ('societal_impact', 'TEXT DEFAULT \'\''),
    ]
    
    print(f"🔍 Checking columns in {table_name}...")
    
    with transaction.atomic():
        for column_name, column_def in columns_to_add:
            if not check_column_exists(table_name, column_name):
                print(f"➕ Adding missing column: {column_name}")
                with connection.cursor() as cursor:
                    sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}'
                    print(f"   SQL: {sql}")
                    cursor.execute(sql)
                print(f"✅ Column {column_name} added successfully")
            else:
                print(f"✅ Column {column_name} already exists")
    
    print("🎉 All columns verified/added successfully!")


if __name__ == '__main__':
    print("🔧 DecipherWorld Production Database Fix")
    print("=" * 50)
    
    try:
        add_missing_columns()
        print("\n✅ Database fix completed successfully!")
        print("The Constitution game should now work on production.")
        
    except Exception as e:
        print(f"\n❌ Error during database fix: {e}")
        print("Please check the database connection and permissions.")
        sys.exit(1)