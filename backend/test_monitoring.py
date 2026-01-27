import requests
import json

# Test the monitoring API with a real user token
# First, get a token by logging in
login_url = "http://localhost:8000/api/auth/login"
monitoring_url = "http://localhost:8000/api/monitoring/overview"

# Login
login_data = {
    "username": "demo@test.com",
    "password": "demopass"
}

print("Logging in as demo@test.com...")
response = requests.post(login_url, json=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json().get("access_token")
    print(f"Got token: {token[:20]}...")
    
    # Test monitoring endpoint
    headers = {"Authorization": f"Bearer {token}"}
    print("\nCalling monitoring/overview endpoint...")
    mon_response = requests.get(monitoring_url, headers=headers)
    print(f"Monitoring status: {mon_response.status_code}")
    
    if mon_response.status_code == 200:
        data = mon_response.json()
        print(f"\nResponse:")
        print(f"  Total containers: {data.get('total_containers')}")
        print(f"  Running containers: {data.get('running_containers')}")
        print(f"  Total CPU: {data.get('total_cpu_percent')}%")
        print(f"  Total Memory: {data.get('total_memory_usage_mb')} MB")
        print(f"  Container stats count: {len(data.get('containers_stats', []))}")
        
        if len(data.get('containers_stats', [])) > 0:
            print("\nFirst container stats:")
            first = data['containers_stats'][0]
            print(f"    Name: {first['name']}")
            print(f"    CPU: {first['cpu_percent']}%")
            print(f"    Memory: {first['memory_usage_mb']} MB")
    else:
        print(f"Error: {mon_response.text}")
else:
    print(f"Login failed: {response.text}")
