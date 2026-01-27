"""
Manual test to verify auto-scaler service works
"""
import sys
sys.path.insert(0, '/app')

from app.database.session import SessionLocal
from app.services.docker_service import DockerService
from app.services.autoscaler_service import AutoScalerService

def test_autoscaler():
    print("Testing Auto-Scaler Service...")
    
    db = SessionLocal()
    docker_service = DockerService()
    autoscaler = AutoScalerService(db, docker_service)
    
    print("Evaluating all policies...")
    autoscaler.evaluate_all_policies()
    
    db.close()
    print("Done!")

if __name__ == "__main__":
    test_autoscaler()
