"""Test script to validate strands imports work correctly."""

print("\n" + "="*60)
print("STRANDS IMPORT TEST")
print("="*60 + "\n")

tests = []

# Test 1: Basic strands imports
try:
    from strands import Agent, tool
    tests.append(("✅", "from strands import Agent, tool"))
except ImportError as e:
    tests.append(("❌", f"from strands import Agent, tool: {e}"))

# Test 2: strands_tools import (the problematic one)
try:
    from strands_tools import http_request, current_time
    tests.append(("✅", "from strands_tools import http_request, current_time"))
except ImportError as e:
    tests.append(("❌", f"from strands_tools: {e}"))

# Test 3: Check strands_tools module
try:
    import strands_tools
    tests.append(("✅", f"strands_tools module found at: {strands_tools.__file__}"))
    tests.append(("📦", f"strands_tools contents: {[x for x in dir(strands_tools) if not x.startswith('_')]}"))
except ImportError as e:
    tests.append(("❌", f"strands_tools module: {e}"))

# Test 4: Check strands.tools
try:
    import strands.tools
    tests.append(("✅", f"strands.tools found at: {strands.tools.__file__}"))
except ImportError as e:
    tests.append(("❌", f"strands.tools: {e}"))

for status, msg in tests:
    print(f"{status} {msg}")

print("\n" + "="*60 + "\n")
