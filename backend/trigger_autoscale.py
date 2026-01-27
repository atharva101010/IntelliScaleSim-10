"""
Simple script to manually trigger auto-scaling evaluation
"""
import requests

# Your auth token - replace with actual token
# For testing: login at http://localhost:5173 and get token from browser dev tools -> Application -> Local Storage
TOKEN = "your_token_here"  # You'll need to get this from the browser

# API endpoint
url = "http://localhost:8000/autoscaling/evaluate-now"

# Make request
headers = {"Authorization": f"Bearer {TOKEN}"}

print("Triggering manual policy evaluation...")
try:
    response = requests.post(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
