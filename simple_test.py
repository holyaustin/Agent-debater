#!/usr/bin/env python3
# ~/Dapps-Empty/2025/Dec2025/agentbeat-tutorial/simple_test.py
import requests
import json
import sys
import os

def check_health(port, name):
    """Check if an agent is healthy"""
    url = f"http://127.0.0.1:{port}/health"
    try:
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ {name} (port {port}): Healthy - {data}")
            return True
        else:
            print(f"❌ {name} (port {port}): Status {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name} (port {port}): {e}")
        return False

def test_debater(port, role):
    """Test a debater"""
    url = f"http://127.0.0.1:{port}/"
    message = f"Debate Topic: Should AI be regulated? Present your opening argument as {role} side."
    
    print(f"\n🧪 Testing {role} debater...")
    
    try:
        resp = requests.post(
            url,
            json={"message": message},
            timeout=10
        )
        
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                
                if isinstance(data, dict) and data.get("status") == "completed":
                    print(f"   ✅ {role} debater works!")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response format")
            except:
                print(f"   ❌ Not valid JSON: {resp.text[:100]}")
        else:
            print(f"   ❌ Error: {resp.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
    
    return False

def main():
    print("="*60)
    print("🧪 MANUAL DEBATE AGENT TEST")
    print("="*60)
    
    # Check all agents are running
    print("\n1. Checking health endpoints:")
    agents = [
        (9009, "Judge"),
        (9019, "Pro Debater"),
        (9018, "Con Debater")
    ]
    
    all_healthy = True
    for port, name in agents:
        if not check_health(port, name):
            all_healthy = False
    
    if not all_healthy:
        print("\n❌ Some agents are not healthy. Please start them first.")
        print("\nStart agents in separate terminals:")
        print("  Terminal 1: cd ~/Dapps-Empty/2025/Dec2025/agentbeat-tutorial && source .venv/bin/activate && python scenarios/debate/debate_judge.py --host 127.0.0.1 --port 9009")
        print("  Terminal 2: cd ~/Dapps-Empty/2025/Dec2025/agentbeat-tutorial && source .venv/bin/activate && python scenarios/debate/debater.py --host 127.0.0.1 --port 9019 --role pro")
        print("  Terminal 3: cd ~/Dapps-Empty/2025/Dec2025/agentbeat-tutorial && source .venv/bin/activate && python scenarios/debate/debater.py --host 127.0.0.1 --port 9018 --role con")
        sys.exit(1)
    
    # Test debaters
    print("\n2. Testing debater communication:")
    pro_ok = test_debater(9019, "Pro")
    con_ok = test_debater(9018, "Con")
    
    print("\n" + "="*60)
    if pro_ok and con_ok:
        print("✅ SUCCESS: Both debaters are working correctly!")
        print("\nNext steps:")
        print("1. The judge should be able to orchestrate a debate")
        print("2. Run: uv run agentbeats-run scenarios/debate/scenario.toml")
    else:
        print("❌ ISSUE: Some debaters are not responding correctly")
        print("\nTroubleshooting:")
        print("1. Check agent logs for errors")
        print("2. Verify Groq API key in .env file")
        print("3. Make sure agents return: {\"status\": \"completed\", \"response\": \"...\", \"context_id\": \"...\"}")

if __name__ == "__main__":
    main()