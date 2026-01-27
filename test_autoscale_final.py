"""
Complete Auto-Scaling Test - Create Container + Policy + Monitor Events
"""
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Login with existing test user
print("=== Logging in ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "autoscale_tester@test.com",
        "password": "TestPassword123!"
    }
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"Details: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in successfully\n")

# 2. Create a test container
print("=== Creating test container ===")
container_data = {
    "name": "autoscale-test-container",
    "image": "nginx:latest",
    "port": 8080,
    "cpu_limit": 500,  # CPU in millicores (500 = 0.5 cores)
    "memory_limit": 256,  # Memory in MB
    "deployment_type": "simulated"
}

container_response = requests.post(
    f"{BASE_URL}/containers/deploy",
    headers=headers,
    json=container_data
)

if container_response.status_code not in [200, 201]:
    print(f"✗ Error creating container: {container_response.status_code}")
    print(f"Details: {container_response.text}")
    exit(1)

container = container_response.json()
container_id = container["id"]
print(f"✓ Container created!")
print(f"  ID: {container_id}")
print(f"  Name: {container['name']}")
print(f"  Status: {container['status']}\n")

# 3. Create auto-scaling policy
print("=== Creating auto-scaling policy ===")
policy_data = {
    "container_id": container_id,
    "scale_up_cpu_threshold": 10.0,  # Simulated CPU range: 3-15%
    "scale_up_memory_threshold": 20.0,  # Simulated Memory range: 10-30%
    "scale_down_cpu_threshold": 5.0,
    "scale_down_memory_threshold": 15.0,
    "min_replicas": 1,
    "max_replicas": 3,
    "cooldown_period": 60,
    "evaluation_period": 60,
    "enabled": True,
    "load_balancer_enabled": False
}

policy_response = requests.post(
    f"{BASE_URL}/autoscaling/policies",
    headers=headers,
    json=policy_data
)

if policy_response.status_code != 200:
    print(f"✗ Error creating policy: {policy_response.status_code}")
    print(f"Details: {policy_response.text}")
    exit(1)

policy = policy_response.json()
print("✓ Policy created successfully!")
print(f"  Policy ID: {policy['id']}")
print(f"  Container ID: {policy['container_id']}")
print(f"  Scale Up Thresholds: CPU >{policy['scale_up_cpu_threshold']}% OR Memory >{policy['scale_up_memory_threshold']}%")
print(f"  Min/Max Replicas: {policy['min_replicas']}-{policy['max_replicas']}")
print(f"  Enabled: {policy['enabled']}\n")

# 4. Trigger immediate evaluation
print("=== Triggering immediate evaluation ===")
eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
if eval_response.status_code == 200:
    print(f"✓ {eval_response.json()['message']}\n")

# 5. Wait for background task (90 seconds = 3 cycles at 30s each)
print("="*70)
print("WAITING 90 SECONDS FOR AUTO-SCALER BACKGROUND TASK")
print("="*70)
print("Background task runs every 30 seconds")
print("With simulated metrics (CPU: 3-15%, Memory: 10-30%) and aggressive")
print(f"thresholds (CPU: {policy_data['scale_up_cpu_threshold']}%, Memory: {policy_data['scale_up_memory_threshold']}%), scaling events are LIKELY!\n")

for i in range(9):
    remaining = 90 - (i * 10)
    status_marker = "█" * (9 - i) + "░" * i
    print(f"  [{status_marker}] {remaining}s remaining...")
    time.sleep(10)

print(f"  [{'░'*9}] Complete!\n")

# 6. Check for scaling events
print("="*70)
print("CHECKING SCALING EVENTS")
print("="*70)
events_response = requests.get(
    f"{BASE_URL}/autoscaling/events",
    headers=headers,
    params={"container_id": container_id, "limit": 20}
)

events = events_response.json()

if len(events) == 0:
    print("⚠ No scaling events found")
    print("\nThis could mean:")
    print("  • Random metrics stayed below thresholds in all 3 cycles")
    print("  • Background task encountered an error")
    print("  • Auto-scaler service is not running")
    print("\n🔍 Triggering one more manual evaluation...")
    
    final_eval = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
    print(f"   Response: {final_eval.json()}")
    
    # Check events again
    print("\n🔍 Checking events one more time...")
    time.sleep(2)
    events_response2 = requests.get(
        f"{BASE_URL}/autoscaling/events",
        headers=headers,
        params={"container_id": container_id, "limit": 20}
    )
    events = events_response2.json()
    
    if len(events) > 0:
        print(f"✓ Found {len(events)} event(s) after manual trigger!")
    else:
        print("❌ Still no events - check backend logs for errors")
else:
    print(f"🎉 SUCCESS! Found {len(events)} scaling event(s)!\n")

# Display events
if events:
    for idx, event in enumerate(events, 1):
        action_emoji = "📈" if event['action'] == 'scale_up' else "📉"
        print(f"{action_emoji} Event #{idx}:")
        print(f"   ID: {event['id']}")
        print(f"   Action: {event['action'].upper()}")
        print(f"   Trigger: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"   Replicas: {event['replica_count_before']} → {event['replica_count_after']}")
        print(f"   Time: {event['created_at']}")
        print()

# 7. Check replica containers
print("="*70)
print("CHECKING REPLICA CONTAINERS")
print("="*70)
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]

main_container = next((c for c in all_containers if c["id"] == container_id), None)
replicas = [c for c in all_containers if c.get("parent_id") == container_id]

if main_container:
    print(f"📦 Main: {main_container['name']} (ID: {container_id}, Status: {main_container['status']})")

if replicas:
    print(f"\n✓ Found {len(replicas)} replica(s):")
    for r in replicas:
        print(f"   • {r['name']} (ID: {r['id']}, Status: {r['status']}, Port: {r.get('port', 'N/A')})")
else:
    print("\nNo replicas created yet")
    if events:
        print("⚠ Events exist but no replicas found - check container creation logic")

print("\n" + "="*70)
print("✅ API TEST COMPLETE")
print("="*70)
print(f"\nContainer ID: {container_id}")
print(f"Policy ID: {policy['id']}")
print(f"Events: {len(events)}")
print(f"Replicas: {len(replicas)}")
print("\n📊 Review backend logs for detailed auto-scaler execution info")
print("🌐 Next: Test UI at http://localhost:5173/admin/autoscaling")
