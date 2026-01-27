"""
Database Cleanup - PostgreSQL Version
Syncs container status with actual Docker containers
"""
import subprocess
import psycopg2

def get_running_docker_containers():
    """Get list of all running Docker container IDs"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.ID}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            containers = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
            return set(containers)
        return set()
    except Exception as e:
        print(f"Error: {e}")
        return set()

def cleanup():
    """Sync database with Docker"""
    
    # Get running containers
    docker_ids = get_running_docker_containers()
    print(f"\n🐳 Found {len(docker_ids)} running containers in Docker")
    print("="*60)
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname="intelliscalesim",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Get all running containers from DB
        cursor.execute("SELECT id, name, container_id FROM containers WHERE status = 'running'")
        db_containers = cursor.fetchall()
        
        print(f"📊 Found {len(db_containers)} containers marked as 'running' in DB\n")
        
        updated = 0
        for db_id, name, container_id in db_containers:
            if not container_id:
                print(f"⚠️  {name} - No Docker ID, skipping")
                continue
            
            if container_id not in docker_ids:
                print(f"🔄 {name} - Not in Docker, marking as stopped")
                cursor.execute("UPDATE containers SET status = 'stopped' WHERE id = %s", (db_id,))
                updated += 1
            else:
                print(f"✅ {name} - Running")
        
        if updated > 0:
            conn.commit()
            print(f"\n✅ Updated {updated} container(s)")
        else:
            print(f"\n✅ All records in sync!")
        
        # Final count
        cursor.execute("SELECT COUNT(*) FROM containers WHERE status = 'running'")
        final_count = cursor.fetchone()[0]
        
        print(f"\n📊 Final Status:")
        print(f"   DB Running: {final_count}")
        print(f"   Docker Running: {len(docker_ids)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

if __name__ == "__main__":
    print("\n🔧 Database Cleanup (PostgreSQL)")
    print("="*60)
    cleanup()
    print("\n✅ Done!")
