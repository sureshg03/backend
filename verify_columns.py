"""
Script to verify all alumni_profiles columns exist
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
from admin_portal.models import AlumniProfile

def verify_columns():
    # Get all fields from the Django model
    model_fields = [field.name for field in AlumniProfile._meta.get_fields() 
                    if hasattr(field, 'column') or field.name == 'regno']
    
    print(f"Django model expects these fields: {model_fields}")
    
    # Get actual columns from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'alumni_profiles'
            ORDER BY ORDINAL_POSITION
        """)
        db_columns = [row[0] for row in cursor.fetchall()]
        
    print(f"\nDatabase has these columns: {db_columns}")
    
    # Check for missing columns
    missing_in_db = set(model_fields) - set(db_columns)
    missing_in_model = set(db_columns) - set(model_fields)
    
    if missing_in_db:
        print(f"\n⚠ Columns defined in model but missing in database: {missing_in_db}")
    else:
        print("\n✓ All model fields exist in database")
        
    if missing_in_model:
        print(f"\n⚠ Columns in database but not in model: {missing_in_model}")
    
    return len(missing_in_db) == 0

if __name__ == "__main__":
    success = verify_columns()
    sys.exit(0 if success else 1)
