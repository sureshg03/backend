# Fix for "Unknown column 'alumni_profiles.profile_picture_url' in 'field list'" Error

## Problem
The `alumni_profiles` table in your database is missing the `profile_picture_url` column that the Django model expects.

## Solution 1: Add the missing column directly (Quickest)

Run this SQL command in your MySQL/MariaDB database:

```sql
ALTER TABLE alumni_profiles 
ADD COLUMN profile_picture_url VARCHAR(255) DEFAULT NULL
AFTER regno;
```

### To run this:
1. Open MySQL Workbench or your database tool
2. Connect to your `admin_db` database
3. Run the above SQL command

OR

Run from command line:
```bash
mysql -u your_username -p admin_db -e "ALTER TABLE alumni_profiles ADD COLUMN profile_picture_url VARCHAR(255) DEFAULT NULL AFTER regno;"
```

## Solution 2: Django Migrations (Recommended for production)

If you want Django to manage this properly, you need to ensure your migrations are in sync. However, since you're using an existing database (not managed by Django migrations initially), you might need to fake the migrations.

## Verification

After adding the column, verify it exists:
```sql
DESCRIBE alumni_profiles;
```

You should see `profile_picture_url` in the column list.

## Restart Your Server

After fixing the database, restart your Django development server:
```bash
cd backend
python manage.py runserver
```
