"""
Script to add missing profile_picture_url column to alumni_profiles table
Run this with: python add_missing_column.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def add_missing_column():
    with connection.cursor() as cursor:
        try:
            # Check if column exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'alumni_profiles'
                AND COLUMN_NAME = 'profile_picture_url'
            """)
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                print("Column 'profile_picture_url' does not exist. Adding it now...")
                cursor.execute("""
                    ALTER TABLE alumni_profiles 
                    ADD COLUMN profile_picture_url VARCHAR(255) DEFAULT NULL
                    AFTER regno
                """)
                print("✓ Column 'profile_picture_url' added successfully!")
            else:
                print("✓ Column 'profile_picture_url' already exists.")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    add_missing_column()
