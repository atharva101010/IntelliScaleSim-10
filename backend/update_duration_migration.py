"""
Update load_tests table duration constraint to allow up to 300 seconds
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.session import engine

def run_migration():
    print("Updating load_tests duration constraint...")
    
    with engine.connect() as connection:
        # Drop old constraint
        connection.execute(text(
            "ALTER TABLE load_tests DROP CONSTRAINT IF EXISTS load_tests_duration_seconds_check"
        ))
        connection.commit()
        print("✓ Dropped old constraint")
        
        # Add new constraint
        connection.execute(text(
            "ALTER TABLE load_tests ADD CONSTRAINT load_tests_duration_seconds_check CHECK (duration_seconds BETWEEN 10 AND 300)"
        ))
        connection.commit()
        print("✓ Added new constraint (10-300 seconds)")
        
        # Verify
        result = connection.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'load_tests'::regclass AND conname LIKE '%duration%'"
        ))
        for row in result:
            print(f"✓ Constraint: {row[0]} - {row[1]}")
    
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
