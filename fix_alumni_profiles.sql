-- Check and add missing column to alumni_profiles table
ALTER TABLE alumni_profiles 
ADD COLUMN IF NOT EXISTS profile_picture_url VARCHAR(255) DEFAULT NULL;

-- Verify the column exists
DESCRIBE alumni_profiles;
