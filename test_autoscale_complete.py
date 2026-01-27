"""
Auto-Scaling API Test with Fresh User Registration
"""
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Register a new admin user
print("=== Registering new admin user ===")
register_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "name": "Autoscale Tester",
        "email": "autoscale_tester@test.com",
        "password": "TestPassword123!",
        "role": "admin"
    }
)

if register_response.status_code != 200:
    print(f"Registration response: {register_response.status_code}")
    print(f"Details: {register_response.text}")
    # Try to login anyway in case user already exists
else:
    print("✓ User registered\n")

# 2. Login
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

# 3. Check existing policies
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

# 4. Create new policy
print("=== Creating new auto-scaling policy ===")
policy_data = {
    "container_id": 18,
    "scale_up_cpu_threshold": 10.0,  # Simulated CPU is 3-15%
    "scale_up_memory_threshold": 20.0,  # Simulated Memory is 10-30%
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
    print(f"  Scale Up: CPU >{new_policy['scale_up_cpu_threshold']}% OR Memory >{new_policy['scale_up_memory_threshold']}%")
    print(f"  Enabled: {new_policy['enabled']}\n")
else:
    print(f"✗ Error creating policy: {create_response.status_code}")
    print(f"Response: {create_response.text}")
    exit(1)

# 5. Trigger manual evaluation immediately
print("=== Triggering manual evaluation #1 ===")
eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
if eval_response.status_code == 200:
    print(f"✓ {eval_response.json()['message']}\n")

# 6. Wait for background task (3 cycles at 30s each)
print("=== Waiting 90 seconds for auto-scaler background task ===")
print("With aggressive thresholds (CPU: 10%, Memory: 20%) and simulated metrics")
print("(CPU: 3-15%, Memory: 10-30%), scaling events should occur!\n")

for i in range(9):
    remaining = 90 - (i * 10)
    print(f"  {remaining}s remaining...")
    time.sleep(10)
print()

# 7. Check for scaling events
print("=== Checking for scaling events ===")
events_response = requests.get(
    f"{BASE_URL}/autoscaling/events",
    headers=headers,
    params={"container_id": 18, "limit": 20}
)

events = events_response.json()
if len(events) == 0:
    print("⚠ No scaling events found yet")
    print("\nPossible reasons:")
    print("  1. Random metrics haven't crossed thresholds in any cycle")
    print("  2. Background task encountered an error (check backend logs)")
    print("  3. Container 18 might not be owned by this user")
    
    # Trigger one more manual evaluation
    print("\n=== Triggering manual evaluation #2 as final test ===")
    eval_response2 = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
    print(f"Response: {eval_response2.json()}")
    
else:
    print(f"✓ SUCCESS! Found {len(events)} scaling event(s)!\n")
    for idx, event in enumerate(events, 1):
        print(f"Event #{idx}:")
        print(f"  ID: {event['id']}")
        print(f"  Action: {event['action'].upper()}")
        print(f"  Trigger: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"  Replicas: {event['replica_count_before']} → {event['replica_count_after']}")
        print(f"  Time: {event['created_at']}")
        print()

# 8. Check current containers and replicas
print("=== Checking replica containers ===")
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]

main_container = next((c for c in all_containers if c["id"] == 18), None)
replicas = [c for c in all_containers if c.get("parent_id") == 18]

if main_container:
    print(f"Main container: {main_container['name']} (ID: 18, Status: {main_container['status']})")
else:
    print("⚠ Could not find container 18 (might be owned by different user)")

if replicas:
    print(f"\n✓ Found {len(replicas)} replica(s) created by auto-scaler:")
    for r in replicas:
        print(f"  - {r['name']} (ID: {r['id']}, Status: {r['status']}, Port: {r.get('port')})")
else:
    print("No replicas created (expected if no scale-up event occurred)")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nNext step: Test via UI at http://localhost:5173/admin/autoscaling")
print("(Note: UI may have authentication issues based on browser testing)")
