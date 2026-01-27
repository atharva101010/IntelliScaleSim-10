"""
Auto-Scaling Feature Test Guide

This script helps you test the auto-scaling feature by generating load on a container.
"""

import time
import requests

def test_autoscaling():
    """
    Guide for testing auto-scaling feature
    """
    
    print("=" * 60)
    print("AUTO-SCALING FEATURE TEST GUIDE")
    print("=" * 60)
    
    print("\n📋 STEP 1: Create a Policy")
    print("-" * 60)
    print("1. Go to Auto-Scaling page")
    print("2. Click 'Create Policy'")
    print("3. Use these settings for easy testing:")
    print("   - Container: Select a RUNNING container")
    print("   - Scale Up CPU: 10% (low threshold for easy trigger)")
    print("   - Scale Up Memory: 80%")
    print("   - Scale Down CPU: 5%")
    print("   - Scale Down Memory: 30%")
    print("   - Min Replicas: 1")
    print("   - Max Replicas: 3")
    print("   - Cooldown: 60 seconds")
    print("   - Evaluation: 30 seconds")
    print("4. Click 'Create Policy'")
    
    print("\n📊 STEP 2: Monitor the System")
    print("-" * 60)
    print("1. Go to Monitoring page - watch CPU/Memory")
    print("2. Go to Auto-Scaling page - refresh to see events")
    print("3. Watch backend terminal for auto-scaler logs")
    
    print("\n🔥 STEP 3: Generate Load (Optional)")
    print("-" * 60)
    print("To trigger scaling, you need high CPU/Memory usage.")
    print("Options:")
    print("1. Deploy a CPU-intensive app (stress test)")
    print("2. Make many requests to your container")
    print("3. Wait for natural load if container is in use")
    
    print("\n✅ STEP 4: Verify Scaling Works")
    print("-" * 60)
    print("Expected behavior:")
    print("1. When CPU > 10%, auto-scaler creates replicas")
    print("2. Replicas appear in 'Recent Scaling Events'")
    print("3. When CPU < 5%, auto-scaler removes replicas")
    print("4. Events are logged in the UI")
    
    print("\n⚠️  IMPORTANT NOTES")
    print("-" * 60)
    print("1. Background task runs every 30 seconds")
    print("2. Cooldown prevents rapid scaling (60s minimum)")
    print("3. Scaling only happens for RUNNING containers")
    print("4. Check backend logs for detailed info")
    
    print("\n" + "=" * 60)
    print("Ready to test! Follow the steps above.")
    print("=" * 60)

if __name__ == "__main__":
    test_autoscaling()
