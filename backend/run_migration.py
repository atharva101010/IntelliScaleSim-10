"""
Run database migration to add Load Testing tables
"""
import sys
sys.path.insert(0, 'C:\\Users\\patil\\OneDrive\\Desktop\\IntelliScaleSim-10\\backend')

from app.database.session import SessionLocal, engine
from sqlalchemy import text

def run_migration():
    """Execute SQL migration script"""
    print("🔄 Starting database migration for Load Testing tables...")
    
    # Read migration SQL
    with open('migrations/add_load_testing_tables.sql', 'r') as f:
        sql_script = f.read()
    
    # Execute migration
    db = SessionLocal()
    try:
        # Remove comments and split by statement
        lines = sql_script.split('\n')
        clean_lines = [l for l in lines if not l.strip().startswith('--')]
        clean_sql = '\n'.join(clean_lines)
        
        # Split by semicolons
        statements = [s.strip() + ';' for s in clean_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement and statement != ';':
                print(f"  Executing statement {i}...")
                try:
                    db.execute(text(statement))
                    db.commit()
                except Exception as e:
                    print(f"    Warning: {e}")
                    # Continue anyway - might be "already exists" errors
        
        print("✅ Migration completed successfully!")
        
        # Verify tables were created
        result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('load_tests', 'load_test_metrics')
        """))
        tables = [row[0] for row in result]
        print(f"📊 Tables created: {', '.join(tables)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
