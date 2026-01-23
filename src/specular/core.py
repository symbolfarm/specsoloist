import os
import re
import json
import urllib.request
import urllib.error
import importlib.resources
import subprocess
from typing import Dict, List, Optional, Any

class SpecularCore:
    def __init__(self, root_dir: str = ".", api_key: Optional[str] = None):
        self.root_dir = os.path.abspath(root_dir)
        self.src_dir = os.path.join(self.root_dir, "src")
        self.build_dir = os.path.join(self.root_dir, "build")
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        # Ensure project directories exist
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)

    def _get_template_content(self, filename: str) -> str:
        """Loads a template from the package resources."""
        # This works whether installed as a package or run locally
        try:
            # Modern importlib.resources (Python 3.9+)
            # Assuming the templates are in 'specular.templates' package
            ref = importlib.resources.files('specular.templates').joinpath(filename)
            return ref.read_text(encoding='utf-8')
        except Exception:
            # Fallback for local dev if package not installed
            local_path = os.path.join(os.path.dirname(__file__), "templates", filename)
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    return f.read()
            return ""

    def _get_spec_path(self, name: str) -> str:
        if not name.endswith(".spec.md"):
            name += ".spec.md"
        return os.path.join(self.src_dir, name)

    def list_specs(self) -> List[str]:
        """Lists all available specification files."""
        specs = []
        if os.path.exists(self.src_dir):
            for root, _, files in os.walk(self.src_dir):
                for file in files:
                    if file.endswith(".spec.md"):
                        specs.append(file)
        return specs

    def read_spec(self, name: str) -> str:
        """Reads the content of a specification file."""
        path = self._get_spec_path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Spec {name} not found.")
        with open(path, 'r') as f:
            return f.read()

    def create_spec(self, name: str, description: str, type: str = "function") -> str:
        """Creates a new specification file from the template."""
        path = self._get_spec_path(name)
        if os.path.exists(path):
            raise FileExistsError(f"Spec {name} already exists.")

        content = self._get_template_content("spec_template.md")
        if not content:
            # Emergency fallback
            content = "---\nname: {name}\n---\n# Overview\n{description}\n"

        # Simple replacement for placeholders
        content = content.replace("[Component Name]", name)
        content = content.replace("[Brief summary of the component's purpose.]", description)
        content = content.replace("type: [function | class | module]", f"type: {type}")

        with open(path, 'w') as f:
            f.write(content)
        
        return f"Created spec: {path}"

    def validate_spec(self, name: str) -> Dict[str, Any]:
        """
        Validates the spec for basic structure and SRS compliance.
        """
        try:
            content = self.read_spec(name)
        except FileNotFoundError:
            return {"valid": False, "errors": ["Spec file not found."]}

        errors = []
        
        # 1. Check Frontmatter
        if not content.strip().startswith("---"):
            errors.append("Missing YAML frontmatter.")
        
        # 2. Check Sections
        required_sections = [
            "# 1. Overview",
            "# 2. Interface Specification",
            "# 3. Functional Requirements",
            "# 4. Non-Functional Requirements",
            "# 5. Design Contract"
        ]
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: '{section}'")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def compile_spec(self, name: str, model: str = "gemini-2.0-flash") -> str:
        """Compiles a spec to code using the LLM."""
        # 1. Validate first
        validation = self.validate_spec(name)
        if not validation["valid"]:
            raise ValueError(f"Cannot compile invalid spec: {validation['errors']}")

        content = self.read_spec(name)
        
        # 2. Parse Frontmatter
        language = "python"
        match = re.search(r"language_target:\s*(\w+)", content)
        if match:
            language = match.group(1)

        # 3. Construct Prompt
        global_context = self._get_template_content("global_context.md")
        
        # Strip frontmatter
        prompt_content = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                prompt_content = parts[2].strip()

        prompt = f"""
You are an expert {language} developer.
Your task is to implement the code described in the following specification.

# Global Project Context
{global_context}

# Component Specification
{prompt_content}

# Instructions
1. Implement the component exactly as described in the Functional Requirements.
2. Adhere strictly to the Non-Functional Requirements (Performance, Purity).
3. Ensure the code satisfies the Design Contract (Pre/Post-conditions).
4. Output ONLY the raw code for the implementation. Do not wrap in markdown code blocks.
"""
        
        # 4. Call LLM
        code = self._call_google_llm(prompt, model)
        
        # 5. Write Output
        output_filename = name.replace(".spec.md", "") + (".py" if language == "python" else ".txt")
        output_path = os.path.join(self.build_dir, output_filename)
        
        with open(output_path, 'w') as f:
            f.write(code)
            
        return f"Compiled to {output_path}"

    def compile_tests(self, name: str, model: str = "gemini-2.0-flash") -> str:
        """Generates a test file for the spec using the LLM."""
        content = self.read_spec(name)
        
        # 2. Parse Frontmatter
        language = "python" # Default
        match = re.search(r"language_target:\s*(\w+)", content)
        if match:
            language = match.group(1)
            
        module_name = name.replace(".spec.md", "")
        
        prompt_content = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                prompt_content = parts[2].strip()

        prompt = f"""
You are an expert QA Engineer specialized in {language}.
Your task is to write a comprehensive unit test suite for the component described below.

# Component Specification
{prompt_content}

# Instructions
1. Write a standard test file (e.g., using `pytest` for Python).
2. The component implementation will be in a module named `{module_name}`. Import it like `from {module_name} import ...`.
3. Implement a test case for EVERY scenario listed in the 'Test Scenarios' section of the spec.
4. Implement additional edge cases based on the 'Design Contract' (Pre/Post-conditions).
5. Output ONLY the raw code.
"""

        code = self._call_google_llm(prompt, model)
        
        output_filename = f"test_{module_name}.py"
        output_path = os.path.join(self.build_dir, output_filename)
        
        with open(output_path, 'w') as f:
            f.write(code)
            
        return f"Generated tests at {output_path}"

    def run_tests(self, name: str) -> Dict[str, Any]:
        """Runs the tests for a specific component."""
        module_name = name.replace(".spec.md", "")
        test_file = f"test_{module_name}.py"
        test_path = os.path.join(self.build_dir, test_file)
        
        if not os.path.exists(test_path):
            return {"success": False, "output": "Test file not found. Run compile_tests() first."}

        # Run pytest on the specific file
        # We add self.build_dir to PYTHONPATH so the tests can import the module
        env = os.environ.copy()
        env["PYTHONPATH"] = self.build_dir + os.pathsep + env.get("PYTHONPATH", "")

        try:
            # Check if pytest is available
            cmd = ["pytest", test_path]
            # If running in uv, we might need 'uv run pytest' but assuming we are in a venv or global
            # For robustness in this prototype, let's try calling it.
            
            result = subprocess.run(
                cmd, 
                env=env, 
                capture_output=True, 
                text=True,
                check=False # We handle return code manually
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + "\n" + result.stderr
            }
        except FileNotFoundError:
             return {"success": False, "output": "pytest command not found."}

    def attempt_fix(self, name: str, model: str = "gemini-2.0-flash") -> str:
        """
        Attempts to fix a failing component by analyzing the test output
        and rewriting either the Code or the Test file.
        """
        # 1. Run Tests first to get the error
        result = self.run_tests(name)
        if result["success"]:
            return "Tests already passed. No fix needed."

        error_log = result["output"]
        spec_content = self.read_spec(name)
        
        module_name = name.replace(".spec.md", "")
        code_path = os.path.join(self.build_dir, f"{module_name}.py")
        test_path = os.path.join(self.build_dir, f"test_{module_name}.py")
        
        code_content = ""
        if os.path.exists(code_path):
            with open(code_path, "r") as f:
                code_content = f.read()

        test_content = ""
        if os.path.exists(test_path):
            with open(test_path, "r") as f:
                test_content = f.read()

        # 2. Construct Analysis Prompt
        prompt = f"""
You are a Senior Software Engineer tasked with fixing a build failure.
Analyze the discrepancy between the Code, the Test, and the Specification.

# 1. The Specification (Source of Truth)
{spec_content}

# 2. The Current Implementation ({module_name}.py)
{code_content}

# 3. The Failing Test Suite (test_{module_name}.py)
{test_content}

# 4. The Test Failure Output
{error_log}

# Instructions
1. Analyze why the test failed.
2. Determine if the **Code** is buggy (violates spec) or if the **Test** is wrong (hallucinated expectation).
3. Provide the CORRECTED content for the file that needs fixing.
4. Use the following format for your output so I can apply the patch:

### FILE: build/{module_name}.py
... (full corrected code content) ...
### END

OR

### FILE: build/test_{module_name}.py
... (full corrected test content) ...
### END

Only provide the file(s) that need to change.
"""

        # 3. Call LLM
        response = self._call_google_llm(prompt, model)

        # 4. Apply Fixes
        changes_made = []
        
        # Regex to find file blocks
        # We look for "### FILE: path" ... content ... "### END"
        # Using DOTALL so . matches newlines
        pattern = r"### FILE: (.+?)\n(.*?)### END"
        matches = re.findall(pattern, response, re.DOTALL)
        
        if not matches:
            return f"LLM analyzed the error but provided no formatted fix.\nResponse:\n{response}"

        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()

            # Strip markdown code blocks if the LLM included them inside our FILE markers
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

            # Security check: ensure we are only writing to build dir
            clean_name = os.path.basename(filename)
            target_path = os.path.join(self.build_dir, clean_name)

            with open(target_path, "w") as f:
                f.write(content)
            changes_made.append(clean_name)

        return f"Applied fixes to: {', '.join(changes_made)}. Run tests again to verify."

    def _call_google_llm(self, prompt: str, model: str) -> str:
        if not self.api_key:
            print("WARNING: No API Key found. Returning mock code.")
            return "# Mock Code (Missing API Key)\ndef mock_func(): pass"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1}
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                try:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    if content.startswith("```"):
                        lines = content.split('\n')
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content = "\n".join(lines)
                    return content
                except (KeyError, IndexError):
                    raise ValueError(f"Unexpected API response format: {result}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise RuntimeError(f"Google Gemini API Error {e.code}: {e.reason}\nDetails: {error_body}")
        except Exception as e:
            raise RuntimeError(f"Error calling Google Gemini API: {str(e)}")
