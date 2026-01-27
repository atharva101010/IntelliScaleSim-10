import requests
import json

try:
    response = requests.post(
        "http://localhost:8000/auth/login",
        json={"email": "demo@test.com", "password": "password123"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ LOGIN SUCCESSFUL!")
        data = response.json()
        print(f"Access Token: {data['access_token'][:50]}...")
    else:
        print(f"❌ Login failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
