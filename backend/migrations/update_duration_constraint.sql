-- Migration to update load_tests duration constraint from 60s to 300s

-- Drop the old constraint
ALTER TABLE load_tests DROP CONSTRAINT IF EXISTS load_tests_duration_seconds_check;

-- Add new constraint allowing up to 300 seconds (5 minutes)
ALTER TABLE load_tests ADD CONSTRAINT load_tests_duration_seconds_check 
    CHECK (duration_seconds BETWEEN 10 AND 300);

-- Verify the constraint
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'load_tests'::regclass 
  AND conname LIKE '%duration%';
