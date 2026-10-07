"""Quick test script to reproduce the alert error."""
import requests
import json

url = "http://127.0.0.1:8000/api/alerts/generate"
payload = {"district_id": 1, "state_id": 1, "risk_level": "HIGH", "send_sms": True}

try:
    resp = requests.post(url, json=payload, timeout=15)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
