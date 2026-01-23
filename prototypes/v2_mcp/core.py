import os
import yaml
import json
import urllib.request
import urllib.error
import re
from typing import Dict, List, Optional, Any

class SpecularCore:
    def __init__(self, root_dir: str, api_key: Optional[str] = None):
        self.root_dir = root_dir
        self.src_dir = os.path.join(root_dir, "src")
        self.build_dir = os.path.join(root_dir, "build")
        self.templates_dir = os.path.join(root_dir, "specular") # In this flattened layout for v2
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        # Ensure directories exist
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)

    def _get_spec_path(self, name: str) -> str:
        if not name.endswith(".spec.md"):
            name += ".spec.md"
        return os.path.join(self.src_dir, name)

    def list_specs(self) -> List[str]:
        """Lists all available specification files."""
        specs = []
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

        template_path = os.path.join(self.templates_dir, "spec_template.md")
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
        else:
            # Fallback if template missing
            content = "---\nname: {name}\n---\n# Overview\n{description}\n"

        # Simple replacement for placeholders (can be improved)
        content = content.replace("[Component Name]", name)
        content = content.replace("[Brief summary of the component's purpose.]", description)
        content = content.replace("type: [function | class | module]", f"type: {type}")

        with open(path, 'w') as f:
            f.write(content)
        
        return f"Created spec: {path}"

    def validate_spec(self, name: str) -> Dict[str, Any]:
        """
        Validates the spec for basic structure and SRS compliance.
        Returns a dict with 'valid' (bool) and 'errors' (list).
        """
        content = self.read_spec(name)
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

    def compile_spec(self, name: str, model: str = "gemini-1.5-flash") -> str:
        """Compiles a spec to code using the LLM."""
        # 1. Validate first
        validation = self.validate_spec(name)
        if not validation["valid"]:
            raise ValueError(f"Cannot compile invalid spec: {validation['errors']}")

        content = self.read_spec(name)
        
        # 2. Parse Frontmatter to get language (simple regex for now)
        language = "python" # Default
        match = re.search(r"language_target:\s*(\w+)", content)
        if match:
            language = match.group(1)

        # 3. Construct Prompt
        global_context_path = os.path.join(self.templates_dir, "global_context.md")
        global_context = ""
        if os.path.exists(global_context_path):
            with open(global_context_path, 'r') as f:
                global_context = f.read()

        # Strip frontmatter for prompt
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

    def _call_google_llm(self, prompt: str, model: str) -> str:
        if not self.api_key:
            # Fallback for demo if no key
            print("WARNING: No API Key found. Returning mock code.")
            return "# Mock Code Generated because GEMINI_API_KEY is missing.\ndef mock_func(): pass"

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
                    # Clean markdown
                    if content.startswith("```"):
                        lines = content.split('\n')
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        content = "\n".join(lines)
                    return content
                except (KeyError, IndexError):
                    return "# Error parsing LLM response"
        except Exception as e:
            return f"# API Error: {str(e)}"

# Demo usage if run directly
if __name__ == "__main__":
    core = SpecularCore(".")
    print("Specs:", core.list_specs())
