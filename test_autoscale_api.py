"""
Simple Auto-Scaling API Test
Creates a policy and monitors for scaling events
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# 1. Login
print("=== Logging in ===")
# Login endpoint expects JSON with email and password fields
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "testisqckb@test.com",
        "password": "password"
    }
)
print(f"Login status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in successfully\n")

# 2. Check existing policies
print("=== Checking existing policies ===")
policies_response = requests.get(f"{BASE_URL}/autoscaling/policies", headers=headers)
existing_policies = policies_response.json()
print(f"Found {len(existing_policies)} existing policy/policies")

# Delete existing policy for container 18 if it exists
for policy in existing_policies:
    if policy.get("container_id") == 18:
        print(f"Deleting existing policy {policy['id']} for container 18...")
        requests.delete(f"{BASE_URL}/autoscaling/policies/{policy['id']}", headers=headers)
        print("✓ Deleted\n")

# 3. Create new policy
print("=== Creating new auto-scaling policy ===")
policy_data = {
    "container_id": 18,
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

create_response = requests.post(
    f"{BASE_URL}/autoscaling/policies",
    headers=headers,
    json=policy_data
)

if create_response.status_code == 200:
    new_policy = create_response.json()
    print("✓ Policy created successfully!")
    print(f"  Policy ID: {new_policy['id']}")
    print(f"  Container ID: {new_policy['container_id']}")
    print(f"  Scale Up CPU Threshold: {new_policy['scale_up_cpu_threshold']}%")
    print(f"  Scale Up Memory Threshold: {new_policy['scale_up_memory_threshold']}%")
    print(f"  Enabled: {new_policy['enabled']}\n")
else:
    print(f"✗ Error creating policy: {create_response.status_code}")
    print(f"Response: {create_response.text}")
    exit(1)

# 4. Trigger manual evaluation
print("=== Triggering manual evaluation ===")
eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
print(f"✓ {eval_response.json()['message']}\n")

# 5. Wait for background task
print("=== Waiting 90 seconds for auto-scaler to run ===")
print("(Background task runs every 30 seconds)")
for i in range(90, 0, -10):
    print(f"  {i} seconds remaining...")
    time.sleep(10)
print()

# 6. Check for scaling events
print("=== Checking for scaling events ===")
events_response = requests.get(
    f"{BASE_URL}/autoscaling/events",
    headers=headers,
    params={"container_id": 18, "limit": 10}
)

events = events_response.json()
if len(events) == 0:
    print("⚠ No scaling events found yet")
    print("This could mean:")
    print("  - Simulated metrics haven't crossed thresholds (3-15% CPU, 10-30% Memory)")
    print("  - Background task is still waiting for next cycle")
else:
    print(f"✓ Found {len(events)} scaling event(s)!\n")
    for event in events:
        print(f"Event ID: {event['id']}")
        print(f"  Action: {event['action']}")
        print(f"  Trigger: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"  Replicas: {event['replica_count_before']} → {event['replica_count_after']}")
        print(f"  Time: {event['created_at']}")
        print()

# 7. Check current containers
print("=== Checking replica containers ===")
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]

main_container = next((c for c in all_containers if c["id"] == 18), None)
replicas = [c for c in all_containers if c.get("parent_id") == 18]

if main_container:
    print(f"Main container: {main_container['name']} (Status: {main_container['status']})")
if replicas:
    print(f"✓ Found {len(replicas)} replica(s):")
    for r in replicas:
        print(f"  - {r['name']} (ID: {r['id']}, Status: {r['status']}, Port: {r.get('port')})")
else:
    print("No replicas created yet (normal if no scale-up event occurred)")

print("\n=== Test Complete ===")
