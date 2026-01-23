from core import SpecularCore
import os
import shutil

# Setup
if os.path.exists("test_env"):
    shutil.rmtree("test_env")
os.makedirs("test_env")

# Init
core = SpecularCore("test_env")

# 1. Create Spec
print("Creating spec...")
path = core.create_spec("login", "Handles user login.")
print(f"Created at: {path}")

# 2. List
specs = core.list_specs()
print(f"Specs: {specs}")
assert "login.spec.md" in specs

# 3. Validate (Should fail on default template because sections are placeholders)
print("Validating (Expect Failure)...")
res = core.validate_spec("login")
print(f"Valid: {res['valid']}")
# Note: The template actually HAS the headers, so it might 'pass' the structural check 
# unless we check for placeholder text. My simple validator only checks for headers.
# Let's see.

# 4. Compile (Mock)
print("Compiling...")
# This will print a warning about API key and write a mock file
msg = core.compile_spec("login")
print(msg)

# Verify Output
outfile = "test_env/build/login.py"
if os.path.exists(outfile):
    print(f"Output file exists: {outfile}")
    with open(outfile, 'r') as f:
        print("Content:", f.read())

# Cleanup
# shutil.rmtree("test_env")
