# test_readiness.py
import requests
import time

def check_agent_readiness(url):
    """Check what makes an agent 'ready'"""
    print(f"\nChecking {url}")
    
    # Try different endpoints
    endpoints = ["/health", "/", "/ready", "/healthz", "/status"]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{url}{endpoint}", timeout=2)
            print(f"  {endpoint}: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"  {endpoint}: Error - {e}")
    
    # Also check POST
    try:
        resp = requests.post(url, json={}, timeout=2)
        print(f"  POST /: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"  POST /: Error - {e}")

# Check all agents
agents = [
    "http://127.0.0.1:9009",
    "http://127.0.0.1:9019", 
    "http://127.0.0.1:9018"
]

for agent in agents:
    check_agent_readiness(agent)