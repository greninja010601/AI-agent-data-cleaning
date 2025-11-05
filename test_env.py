from dotenv import load_dotenv
import os
from pathlib import Path

print("="*60)
print("ENVIRONMENT VARIABLE TEST")
print("="*60)

# Check current directory
current_dir = os.getcwd()
print(f"\n1. Current directory: {current_dir}")

# Check if .env exists
env_file = Path('.env')
print(f"2. .env file exists: {env_file.exists()}")

# Try to read .env file content
if env_file.exists():
    print(f"3. .env file size: {env_file.stat().st_size} bytes")
    print("\n4. .env file content:")
    print("-" * 40)
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
        print(repr(content))  # Shows hidden characters
    print("-" * 40)

# Load environment variables with verbose output
print("\n5. Loading .env file...")
result = load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

# Check if variable is loaded
print("\n6. Checking GOOGLE_API_KEY...")
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    print("   ✓ SUCCESS! API key loaded")
    print(f"   Key: {api_key[:20]}...{api_key[-10:]}")
else:
    print("   ✗ FAILED! API key NOT found")
    print("\n   All environment variables:")
    for key, value in os.environ.items():
        if 'GOOGLE' in key or 'API' in key:
            print(f"   - {key}: {value[:20]}..." if len(value) > 20 else f"   - {key}: {value}")

print("\n" + "="*60)