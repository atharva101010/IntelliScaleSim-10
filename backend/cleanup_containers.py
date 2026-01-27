"""
Database Cleanup Script
Syncs database container status with actual Docker containers
"""

from app.database.session import SessionLocal
from app.models.container import Container
import subprocess

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
            containers = result.stdout.strip().split('\n')
            return set(c for c in containers if c)  # Filter empty strings
        return set()
    except Exception as e:
        print(f"Error getting Docker containers: {e}")
        return set()

def cleanup_database():
    """Update database to match actual Docker state"""
    db = SessionLocal()
    
    try:
        # Get running containers from Docker
        docker_containers = get_running_docker_containers()
        print(f"\nFound {len(docker_containers)} running containers in Docker")
        print("="*60)
        
        # Get containers marked as running in database
        db_containers = db.query(Container).filter(
            Container.status == 'running'
        ).all()
        
        print(f"Found {len(db_containers)} containers marked as 'running' in database\n")
        
        updated = 0
        for container in db_containers:
            if not container.container_id:
                print(f"⚠️  {container.name} - No Docker ID, skipping")
                continue
                
            # Check if container exists in Docker
            if container.container_id not in docker_containers:
                print(f"🔄 {container.name} - Not found in Docker, marking as stopped")
                container.status = 'stopped'
                updated += 1
            else:
                print(f"✅ {container.name} - Still running")
        
        if updated > 0:
            db.commit()
            print(f"\n✅ Updated {updated} container(s) to 'stopped' status")
        else:
            print(f"\n✅ All database records are in sync!")
        
        # Show final stats
        running_count = db.query(Container).filter(
            Container.status == 'running'
        ).count()
        
        print(f"\n📊 Final Status:")
        print(f"   Running containers in DB: {running_count}")
        print(f"   Running containers in Docker: {len(docker_containers)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔧 Database Cleanup Tool")
    print("="*60)
    cleanup_database()
    print("\n✅ Cleanup complete!")
