# test_env.py
import subprocess
import os

# Test with current environment
print("Current PATH:", os.environ.get('PATH', ''))

# Run command with full environment
result = subprocess.run(
    'uv run python --version',
    shell=True,
    capture_output=True,
    text=True,
    env=os.environ  # Pass current environment
)
print(f"\nWith full environment:")
print(f"Exit code: {result.returncode}")
print(f"Output: {result.stdout.strip()}")