"""
Auto-Scaling Test - Use Existing Container or Create New One
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("="*70)
print("AUTO-SCALING API TEST")
print("="*70)

# 1. Login
print("\n=== Step 1: Logging in ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "autoscale_tester@test.com",
        "password": "TestPassword123!"
    }
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in successfully")

# 2. Get existing containers
print("\n=== Step 2: Finding test container ===")
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]

# Look for our test container
test_container = next((c for c in all_containers if c["name"] == "autoscale-test-container"), None)

if test_container:
    container_id = test_container["id"]
    print(f"✓ Found existing test container")
    print(f"   ID: {container_id}")
    print(f"   Name: {test_container['name']}")
    print(f"   Status: {test_container['status']}")
else:
    # Create new container
    print("Creating new test container...")
    container_data = {
        "name": f"autoscale-test-{int(time.time())}",
        "image": "nginx:latest",
        "port": 8080,
        "cpu_limit": 500,
        "memory_limit": 256,
        "deployment_type": "simulated"
    }
    
    container_response = requests.post(
        f"{BASE_URL}/containers/deploy",
        headers=headers,
        json=container_data
    )
    
    if container_response.status_code not in [200, 201]:
        print(f"✗ Error: {container_response.text}")
        exit(1)
    
    test_container = container_response.json()
    container_id = test_container["id"]
    print(f"✓ Container created (ID: {container_id})")

# 3. Delete old policy if exists
print("\n=== Step 3: Checking existing policies ===")
policies_response = requests.get(f"{BASE_URL}/autoscaling/policies", headers=headers)
existing_policies = policies_response.json()

old_policy = next((p for p in existing_policies if p.get("container_id") == container_id), None)
if old_policy:
    print(f"Deleting existing policy (ID: {old_policy['id']})...")
    requests.delete(f"{BASE_URL}/autoscaling/policies/{old_policy['id']}", headers=headers)
    print("✓ Deleted")
else:
    print("No existing policy for this container")

# 4. Create new policy
print("\n=== Step 4: Creating auto-scaling policy ===")
policy_data = {
    "container_id": container_id,
    "scale_up_cpu_threshold": 10.0,
    "scale_up_memory_threshold": 20.0,
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
    print(f"✗ Error: {policy_response.text}")
    exit(1)

policy = policy_response.json()
print("✓ Policy created successfully!")
print(f"   Policy ID: {policy['id']}")
print(f"   Thresholds: CPU >{policy['scale_up_cpu_threshold']}% OR Memory >{policy['scale_up_memory_threshold']}%")

# 5. Trigger manual evaluation
print("\n=== Step 5: Triggering manual evaluation ===")
eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
print(f"✓ {eval_response.json()['message']}")

# 6. Wait for background task
print("\n" + "="*70)
print("WAITING 90 SECONDS FOR BACKGROUND AUTO-SCALER")
print("="*70)
print(f"Container ID: {container_id}")
print(f"Policy ID: {policy['id']}")
print(f"Simulated Metrics: CPU 3-15%, Memory 10-30%")
print(f"Scale-Up Thresholds: CPU >{policy_data['scale_up_cpu_threshold']}%, Memory >{policy_data['scale_up_memory_threshold']}%")
print(f"\nBackground task runs every 30 seconds...")
print()

for i in range(9):
    remaining = 90 - (i * 10)
    progress_bar = "█" * (9 - i) + "░" * i
    print(f"  [{progress_bar}] {remaining}s...", end='\r')
    time.sleep(10)

print(f"  [{'█'*9}] Done!    \n")

# 7. Check for scaling events
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
    print("\n🔍 Triggering final manual evaluation...")
    requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
    time.sleep(2)
    events_response = requests.get(
        f"{BASE_URL}/autoscaling/events",
        headers=headers,
        params={"container_id": container_id, "limit": 20}
    )
    events = events_response.json()

if events:
    print(f"🎉 SUCCESS! Found {len(events)} scaling event(s)!\n")
    for idx, event in enumerate(events, 1):
        emoji = "📈" if event['action'] == 'scale_up' else "📉"
        print(f"{emoji} Event #{idx}: {event['action'].upper()}")
        print(f"   Trigger: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"   Replicas: {event['replica_count_before']} → {event['replica_count_after']}")
        print(f"   Time: {event['created_at']}")
        print()
else:
    print("❌ No events found after 90+ seconds")
    print("Check backend logs for errors in auto-scaler service")

# 8. Check replica containers
print("="*70)
print("REPLICA CONTAINERS")
print("="*70)
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]
replicas = [c for c in all_containers if c.get("parent_id") == container_id]

if replicas:
    print(f"✓ Found {len(replicas)} replica(s):")
    for r in replicas:
        print(f"   • {r['name']} (ID: {r['id']}, Status: {r['status']})")
else:
    print("No replicas created")

print("\n" + "="*70)
print("✅ TEST COMPLETE")
print("="*70)
print(f"Container ID: {container_id} | Policy ID: {policy['id']}")
print(f"Events: {len(events)} | Replicas: {len(replicas)}")
print("\n📊 Next: Check http://localhost:5173/admin/autoscaling (if UI issues are fixed)")
