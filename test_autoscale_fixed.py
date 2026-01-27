"""
Auto-Scaling Test - Fixed Version
"""
import requests
import time
import json

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

if not test_container:
    print("ERROR - No test container found")
    exit(1)

container_id = test_container["id"]
print(f"OK - Found container ID {container_id}")

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

# Check status code, not response body
if policy_response.status_code not in [200, 201]:
    print(f"ERROR: Policy creation failed ({policy_response.status_code})")
    print(policy_response.text)
    exit(1)

policy = policy_response.json()
print(f"OK - Policy created (ID: {policy['id']})")
print(f"     CPU threshold: >{policy['scale_up_cpu_threshold']}%, Memory: >{policy['scale_up_memory_threshold']}%")

# 5. Trigger manual evaluation
print("\n[5/8] Triggering manual evaluation...")
try:
    eval_response = requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
    result = eval_response.json()
    print(f"OK - {result.get('message', 'Evaluation triggered')}")
except Exception as e:
    print(f"WARNING - Manual trigger failed: {e}")

# 6. Wait for background task (90 seconds = 3 cycles at 30s each)
print("\n[6/8] Waiting 90 seconds for background auto-scaler...")
print(f"     Container: {container_id}, Policy: {policy['id']}")
print(f"     Simulated metrics: CPU 3-15%, Memory 10-30%")
print(f"     Scale-up triggers: CPU>{policy_data['scale_up_cpu_threshold']}% OR Memory>{policy_data['scale_up_memory_threshold']}%")
print(f"     Background task runs every 30 seconds (3 cycles total)\n")

for i in range(9):
    remaining = 90 - (i * 10)
    print(f"     {remaining}s remaining...")
    time.sleep(10)

print(f"     Complete!\n")

# 7. Check for scaling events
print("[7/8] Checking for scaling events...")
try:
    events_response = requests.get(
        f"{BASE_URL}/autoscaling/events",
        headers=headers,
        params={"container_id": container_id, "limit": 20}
    )
    events = events_response.json()
except Exception as e:
    print(f"ERROR: Failed to fetch events: {e}")
    events = []

if len(events) == 0:
    print("WARNING: No scaling events found yet")
    print("Triggering one more manual evaluation...")
    try:
        requests.post(f"{BASE_URL}/autoscaling/evaluate-now", headers=headers)
        time.sleep(3)
        events_response = requests.get(
            f"{BASE_URL}/autoscaling/events",
            headers=headers,
            params={"container_id": container_id, "limit": 20}
        )
        events = events_response.json()
    except Exception as e:
        print(f"ERROR: {e}")
        events = []

if events:
    print(f"\nSUCCESS: Found {len(events)} scaling event(s)!\n")
    for idx, event in enumerate(events, 1):
        print(f"  Event #{idx}: {event['action'].upper()}")
        print(f"    Metric: {event['trigger_metric']} = {event['metric_value']}%")
        print(f"    Replicas: {event['replica_count_before']} -> {event['replica_count_after']}")
        print(f"    Time: {event['created_at']}")
        print()
else:
    print("\nWARNING: No events found")
    print("Possible reasons:")
    print("  - Random metrics didn't cross thresholds")
    print("  - Background task errors (check backend logs)")

# 8. Check replica containers
print("[8/8] Checking replica containers...")
try:
    containers_response = requests.get(f"{BASE_URL}/containers/", headers=headers)
    all_containers = containers_response.json()["containers"]
    replicas = [c for c in all_containers if c.get("parent_id") == container_id]
    
    if replicas:
        print(f"OK - Found {len(replicas)} replica(s):")
        for r in replicas:
            print(f"     - {r['name']} (ID: {r['id']}, Status: {r['status']})")
    else:
        print("No replicas created (expected if no scale-up event)")
except Exception as e:
    print(f"ERROR: {e}")
    replicas = []

# Final Summary
print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print(f"Container ID: {container_id}")
print(f"Policy ID: {policy['id']}")
print(f"Scaling Events: {len(events)}")
print(f"Replicas Created: {len(replicas) if 'replicas' in locals() else 0}")

if events:
    print("\nRESULT: SUCCESS - Auto-scaling is WORKING!")
    print("The auto-scaler successfully evaluated policies and generated events.")
else:
    print("\nRESULT: PARTIAL - Policy created but no events yet")
    print("You may need to wait longer or check backend logs for errors.")

print("\nNext step: Test UI at http://localhost:5173/admin/autoscaling")
print("(Note: UI may have authentication issues based on browser testing)\n")
