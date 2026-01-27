"""
Auto-Scaling Test - ASCII Only Version
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("="*70)
print("AUTO-SCALING API TEST")
print("="*70)

# 1. Login
print("\n[1/8] Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "autoscale_tester@test.com", "password": "TestPassword123!"}
)

if login_response.status_code != 200:
    print(f"ERROR: Login failed ({login_response.status_code})")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("OK - Logged in")

# 2. Get existing containers
print("\n[2/8] Finding test container...")
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]
test_container = next((c for c in all_containers if c["name"] == "autoscale-test-container"), None)

if test_container:
    container_id = test_container["id"]
    print(f"OK - Found container ID {container_id}")
else:
    print(f"ERROR - No test container found")
    exit(1)

# 3. Delete old policy if exists
print("\n[3/8] Checking existing policies...")
policies_response = requests.get(f"{BASE_URL}/autoscaling/policies", headers=headers)
existing_policies = policies_response.json()
old_policy = next((p for p in existing_policies if p.get("container_id") == container_id), None)

if old_policy:
    print(f"Deleting old policy {old_policy['id']}...")
    requests.delete(f"{BASE_URL}/autoscaling/policies/{old_policy['id']}", headers=headers)
    print("OK - Deleted")
else:
    print("OK - No existing policy")

# 4. Create new policy
print("\n[4/8] Creating auto-scaling policy...")
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
    print(f"ERROR: {policy_response.text}")
    exit(1)

policy = policy_response.json()
print(f"OK - Policy ID {policy['id']} created")
print(f"     Thresholds: CPU>{policy['scale_up_cpu_threshold']}% OR Memory>{policy['scale_up_memory_threshold']}%")

# 5. Trigger manual evaluation
print("\n[5/8] Triggering manual evaluation...")
eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
print(f"OK - {eval_response.json()['message']}")

# 6. Wait for background task
print("\n[6/8] Waiting 90 seconds for background auto-scaler...")
print(f"     Container: {container_id} | Policy: {policy['id']}")
print(f"     Simulated Metrics: CPU 3-15%, Memory 10-30%")
print(f"     Background task runs every 30 seconds\n")

for i in range(9):
    remaining = 90 - (i * 10)
    dots = "." * (i + 1)
    print(f"     {remaining}s remaining{dots}                ")
    time.sleep(10)

print(f"     Done!                    \n")

# 7. Check for scaling events
print("[7/8] Checking for scaling events...")
events_response = requests.get(
    f"{BASE_URL}/autoscaling/events",
    headers=headers,
    params={"container_id": container_id, "limit": 20}
)

events = events_response.json()

if len(events) == 0:
    print("WARNING: No scaling events found")
    print("Triggering final manual evaluation...")
    requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
    time.sleep(2)
    events_response = requests.get(
        f"{BASE_URL}/autoscaling/events",
        headers=headers,
        params={"container_id": container_id, "limit": 20}
    )
    events = events_response.json()

if events:
    print(f"SUCCESS: Found {len(events)} scaling event(s)!\n")
    for idx, event in enumerate(events, 1):
        print(f"  Event #{idx}: {event['action'].upper()}")
        print(f"    Trigger: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"    Replicas: {event['replica_count_before']} -> {event['replica_count_after']}")
        print(f"    Time: {event['created_at']}")
        print()
else:
    print("ERROR: No events found after 90+ seconds")
    print("Check backend logs for auto-scaler errors")

# 8. Check replica containers
print("[8/8] Checking replica containers...")
containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
all_containers = containers_response.json()["containers"]
replicas = [c for c in all_containers if c.get("parent_id") == container_id]

if replicas:
    print(f"OK - Found {len(replicas)} replica(s):")
    for r in replicas:
        print(f"     - {r['name']} (ID: {r['id']}, Status: {r['status']})")
else:
    print("No replicas created")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print(f"Container: {container_id} | Policy: {policy['id']}")
print(f"Events: {len(events)} | Replicas: {len(replicas)}")

if events:
    print("\nRESULT: SUCCESS - Auto-scaling is working!")
else:
    print("\nRESULT: FAIL - No scaling events generated")
    print("Check backend logs with: cd backend && tail -n 50 uvicorn.log")

print("\nNext: Test UI at http://localhost:5173/admin/autoscaling")
