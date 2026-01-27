from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/intelliscalesim')

with engine.connect() as conn:
    result = conn.execute(text(
        'SELECT id, status, requests_sent, requests_completed, requests_failed, error_message, created_at '
        'FROM load_tests ORDER BY id DESC LIMIT 3'
    ))
    
    print("\n=== Recent Load Tests ===")
    for row in result:
        print(f"\nTest ID: {row[0]}")
        print(f"  Status: {row[1]}")
        print(f"  Requests - Sent: {row[2]}, Completed: {row[3]}, Failed: {row[4]}")
        print(f"  Error: {row[5] or 'None'}")
        print(f"  Created: {row[6]}")
