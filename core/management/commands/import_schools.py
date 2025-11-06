#!/usr/bin/env python3
"""
Management command to import schools from CSV file
Optimized for handling 1M+ records efficiently

Usage:
    python manage.py import_schools path/to/schools.csv
    python manage.py import_schools schools.csv --batch-size 5000 --clean
"""

import csv
import time
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import School


class Command(BaseCommand):
    help = 'Import schools from CSV file (optimized for 1M+ records)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing school data'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete all existing schools before import'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue import even if some records fail'
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Start import from specific row number (useful for resuming)'
        )
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        clean = options['clean']
        skip_errors = options['skip_errors']
        start_from = options['start_from']
        
        # Validate file exists
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        
        # Clean existing data if requested
        if clean:
            self.stdout.write('🗑️  Cleaning existing school data...')
            deleted_count = School.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing schools')
            )
        
        # Import data
        self.stdout.write(f'📂 Starting import from: {csv_file}')
        self.stdout.write(f'⚙️  Batch size: {batch_size}')
        if start_from > 0:
            self.stdout.write(f'⏩ Starting from row: {start_from}')
        
        start_time = time.time()
        
        try:
            imported_count = self.import_schools(
                csv_file, batch_size, skip_errors, start_from
            )
            
            elapsed_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully imported {imported_count} schools '
                    f'in {elapsed_time:.2f} seconds'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Import failed: {str(e)}')
            )
            raise
    
    def import_schools(self, csv_file, batch_size, skip_errors, start_from):
        """Import schools in optimized batches"""
        schools_batch = []
        imported_count = 0
        error_count = 0
        row_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Skip to start_from row
            for _ in range(start_from):
                try:
                    next(reader)
                    row_count += 1
                except StopIteration:
                    break
            
            for row in reader:
                row_count += 1
                
                try:
                    school = self.create_school_from_row(row)
                    if school:
                        schools_batch.append(school)
                    
                    # Process batch when it reaches batch_size
                    if len(schools_batch) >= batch_size:
                        imported_count += self.save_batch(schools_batch)
                        schools_batch = []
                        
                        # Progress update
                        self.stdout.write(
                            f'📊 Processed {row_count} rows, '
                            f'imported {imported_count} schools...'
                        )
                
                except Exception as e:
                    error_count += 1
                    error_msg = f'Row {row_count}: {str(e)}'
                    
                    if skip_errors:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Skipped - {error_msg}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error - {error_msg}')
                        )
                        raise CommandError(f'Import failed at row {row_count}')
            
            # Process remaining batch
            if schools_batch:
                imported_count += self.save_batch(schools_batch)
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Total errors: {error_count}')
            )
        
        return imported_count
    
    def create_school_from_row(self, row):
        """Create School instance from CSV row"""
        # Map CSV columns to model fields
        def safe_int(value, default=None):
            """Safely convert to int"""
            try:
                return int(float(value)) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        def safe_decimal(value, default=None):
            """Safely convert to decimal"""
            try:
                return Decimal(str(value)) if value and str(value).strip() else default
            except (InvalidOperation, TypeError):
                return default
        
        def safe_str(value, max_length=None):
            """Safely convert to string"""
            if not value:
                return ''
            value = str(value).strip()
            if max_length:
                value = value[:max_length]
            return value
        
        # Map management types
        management_map = {
            'government': 'government',
            'private': 'private',
            'aided': 'aided',
            'central': 'central_govt',
            'central government': 'central_govt',
            'private unaided': 'private',
            'government aided': 'aided',
        }
        
        # Map school categories
        category_map = {
            'primary': 'primary',
            'upper primary': 'upper_primary',
            'secondary': 'secondary',
            'higher secondary': 'higher_secondary',
            'pre-primary': 'pre_primary',
            'pre primary': 'pre_primary',
        }
        
        # Map school types
        type_map = {
            'boys': 'boys',
            'girls': 'girls',
            'co-educational': 'co_ed',
            'co-ed': 'co_ed',
            'coeducational': 'co_ed',
        }
        
        # Required fields validation
        school_code = safe_str(row.get('School Code'), 20)
        school_name = safe_str(row.get('School Name'), 200)
        
        if not school_code or not school_name:
            raise ValueError(f'Missing required fields: School Code or School Name')
        
        # Check if school already exists
        if School.objects.filter(school_code=school_code).exists():
            return None  # Skip duplicates
        
        # Create school instance
        school = School(
            # Core identifiers
            school_code=school_code,
            school_name=school_name,
            
            # Location
            state=safe_str(row.get('State'), 100),
            state_code=safe_str(row.get('State Code'), 10),
            district=safe_str(row.get('District'), 100),
            district_code=safe_str(row.get('District Code'), 10),
            sub_district=safe_str(row.get('Sub-District'), 100),
            sub_district_code=safe_str(row.get('Sub-District Code'), 10),
            cluster=safe_str(row.get('Cluster'), 100),
            village=safe_str(row.get('Village'), 100),
            udise_village_code=safe_str(row.get('UDISE Village Code'), 20),
            pincode=safe_str(row.get('Pincode'), 10),
            ward=safe_str(row.get('Ward'), 50),
            
            # Classification
            school_category=category_map.get(
                safe_str(row.get('School Category')).lower(), ''
            ),
            school_type=type_map.get(
                safe_str(row.get('School Type')).lower(), ''
            ),
            management=management_map.get(
                safe_str(row.get('Management')).lower(), ''
            ),
            
            # Basic details
            year_of_establishment=safe_int(row.get('Year of Establishment')),
            longitude=safe_decimal(row.get('Longitude')),
            latitude=safe_decimal(row.get('Latitude')),
            status='functional',  # Default to functional
            location_type='rural' if 'rural' in safe_str(row.get('Location Type')).lower() else 'urban',
            
            # Grade range
            class_from=safe_int(row.get('Class From')),
            class_to=safe_int(row.get('Class To')),
            
            # Affiliation
            affiliation_board_secondary=safe_str(
                row.get('Affiliation Board for Secondary Education'), 100
            ),
            affiliation_board_higher_secondary=safe_str(
                row.get('Affiliation Board for Higher Secondary Education'), 100
            ),
            
            # Infrastructure
            pre_primary_rooms=safe_int(row.get('Pre Primary Rooms'), 0),
            class_rooms=safe_int(row.get('Class Rooms'), 0),
            other_rooms=safe_int(row.get('Other Rooms'), 0),
            teachers=safe_int(row.get('Teachers'), 0),
            
            # Student enrollment
            pre_primary_students=safe_int(row.get('Pre Primary Students'), 0),
            students_class_1=safe_int(row.get('Students in Class I'), 0),
            students_class_2=safe_int(row.get('Students in Class II'), 0),
            students_class_3=safe_int(row.get('Students in Class III'), 0),
            students_class_4=safe_int(row.get('Students in Class IV'), 0),
            students_class_5=safe_int(row.get('Students in Class V'), 0),
            students_class_6=safe_int(row.get('Students in Class VI'), 0),
            students_class_7=safe_int(row.get('Students in Class VII'), 0),
            students_class_8=safe_int(row.get('Students in Class VIII'), 0),
            students_class_9=safe_int(row.get('Students in Class IX'), 0),
            students_class_10=safe_int(row.get('Students in Class X'), 0),
            students_class_11=safe_int(row.get('Students in Class XI'), 0),
            students_class_12=safe_int(row.get('Students in Class XII'), 0),
            non_primary_students=safe_int(row.get('Non Primary Students'), 0),
            total_students=safe_int(row.get('Total Students'), 0),
        )
        
        return school
    
    def save_batch(self, schools_batch):
        """Save batch of schools efficiently using bulk_create"""
        try:
            with transaction.atomic():
                School.objects.bulk_create(
                    schools_batch, 
                    ignore_conflicts=True,  # Skip duplicates
                    batch_size=1000  # PostgreSQL optimization
                )
                return len(schools_batch)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Batch save failed: {str(e)}')
            )
            return 0