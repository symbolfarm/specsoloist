import yaml
import os
import sys

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def construct_prompt(global_context, spec_content, language):
    # Strip YAML frontmatter if present
    if spec_content.startswith("---"):
        try:
            _, _, content = spec_content.split("---", 2)
            spec_content = content.strip()
        except ValueError:
            pass # Malformed frontmatter, use as is

    return f"""
You are an expert {language} developer.
Your task is to implement the code described in the following specification.

# Global Project Context
{global_context}

# Component Specification
{spec_content}

# Instructions
1. Implement the component exactly as described in the Functional Requirements.
2. Adhere strictly to the Non-Functional Requirements (Performance, Purity).
3. Ensure the code satisfies the Design Contract (Pre/Post-conditions).
4. Output ONLY the raw code for the implementation.
"""

def mock_llm_generate(prompt):
    # This is a placeholder that simulates the LLM's output for the slugify spec.
    print("--- MOCK LLM: Receiving Prompt ---")
    print(prompt[:200] + "...\n[Truncated]\n--------------------------------")
    
    return """import unicodedata
import re

def slugify(text: str, separator: str = "-") -> str:
    \"\"\"
    Converts an input string into a URL-friendly "slug".
    \"\"\"
    if not text:
        return ""

    # 1. Normalization
    text = unicodedata.normalize('NFKD', text)
    
    # 2. Filtering (keep ASCII) & 3. Case Conversion
    text = text.encode('ascii', 'ignore').decode('ascii').lower()
    
    # 4. Replacement (replace non-alphanumeric with separator)
    text = re.sub(r'[^a-z0-9]+', separator, text)
    
    # 5. Trimming
    text = text.strip(separator)
    
    # 6. Deduplication
    # Escape separator if it might be a regex special char
    sep_pattern = re.escape(separator)
    text = re.sub(f'{sep_pattern}+', separator, text)
    
    return text
"""

def main():
    config_path = "llm_build.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    global_context_path = config.get('global_context')
    global_context = read_file(global_context_path) if global_context_path else ""

    for target in config.get('targets', []):
        spec_path = target['spec']
        output_path = target['output_path']
        language = target.get('language', 'python')

        print(f"Compiling {spec_path} to {output_path} ({language})...")

        spec_content = read_file(spec_path)
        prompt = construct_prompt(global_context, spec_content, language)

        # In a real scenario, we would switch based on config['llm_config']['provider']
        # For now, we default to mock.
        generated_code = mock_llm_generate(prompt)

        write_file(output_path, generated_code)
        print(f"Generated {output_path}")

if __name__ == "__main__":
    main()
