import requests
import json

# Register a new test user
register_response = requests.post(
    "http://localhost:8000/auth/register",
    json={
        "name": "Test User",
        "email": "loadtest@test.com",
        "password": "password123",
        "role": "student"
    }
)

print(f"Registration: {register_response.status_code}")

# Login
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "loadtest@test.com", "password": "password123"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✓ Login successful")
    
    # Test load test start endpoint
    url = "http://localhost:8000/loadtest/start"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "container_id": 18,
        "total_requests": 100,
        "concurrency": 10,
        "duration_seconds": 30
    }
    
    print(f"\n→ POST {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"← Status: {response.status_code}")
        if response.status_code != 201:
            print(f"← Response: {response.text}")
        else:
            print(f"← Success: {response.json()}")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print(f"✗ Login failed: {login_response.status_code} - {login_response.text}")
