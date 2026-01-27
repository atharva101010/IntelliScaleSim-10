import requests
import json

# Test the load test API
url = "http://localhost:8000/api/loadtest/start"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"  # Test token
}
data = {
    "container_id": 18,
    "total_requests": 100,
    "concurrency": 10,
    "duration_seconds": 30
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
