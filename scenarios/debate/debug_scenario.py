# debug_scenario.py
import subprocess
import time
import requests
import sys

def run_agent(cmd, port, name):
    print(f"\n🚀 Starting {name} on port {port}")
    print(f"Command: {cmd}")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    for i in range(10):
        time.sleep(1)
        print(f"  Waiting... {i+1}s")
        
        # Check if process died
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Process died! Exit code: {process.returncode}")
            print(f"Stdout: {stdout[:200]}")
            print(f"Stderr: {stderr[:200]}")
            return False
        
        # Check health endpoint
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=1)
            if resp.status_code == 200:
                print(f"✅ {name} is healthy!")
                return True
        except:
            pass
    
    print(f"❌ {name} never became healthy")
    process.terminate()
    return False

# Test commands
commands = [
    ("uv run python scenarios/debate/debate_judge.py --host 127.0.0.1 --port 9009", 9009, "Judge"),
    ("uv run python scenarios/debate/debater.py --host 127.0.0.1 --port 9019 --role pro", 9019, "Pro Debater"),
    ("uv run python scenarios/debate/debater.py --host 127.0.0.1 --port 9018 --role con", 9018, "Con Debater"),
]

# Kill existing
import os
os.system("pkill -f 'python.*debate' 2>/dev/null")

# Run all
all_ok = True
for cmd, port, name in commands:
    if not run_agent(cmd, port, name):
        all_ok = False

if all_ok:
    print("\n✅ All agents started successfully!")
    print("Now run: uv run agentbeats-run scenarios/debate/scenario.toml")
else:
    print("\n❌ Some agents failed to start")
    sys.exit(1)