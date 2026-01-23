import yaml
import os
import sys
import json
import urllib.request
import urllib.error

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
4. Output ONLY the raw code for the implementation. Do not wrap in markdown code blocks.
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
    if text is None:
        return ""
    
    # FR-01: Normalize Unicode
    text = unicodedata.normalize('NFKD', text)
    
    # FR-02: Filter non-ASCII
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # FR-03: Lowercase
    text = text.lower()
    
    # FR-04: Replace non-alphanumeric with separator
    text = re.sub(r'[^a-z0-9]+', separator, text)
    
    # FR-05: Trim separator
    text = text.strip(separator)
    
    return text
"""

def google_llm_generate(prompt, model, api_key):
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1
        }
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Extract text from response
            try:
                content = result['candidates'][0]['content']['parts'][0]['text']
                # Clean up markdown code blocks if present (LLMs often add them despite instructions)
                if content.startswith("```"):
                    lines = content.split('\n')
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines)
                return content
            except (KeyError, IndexError):
                print(f"Error parsing Gemini response: {result}")
                return ""
                
    except urllib.error.HTTPError as e:
        print(f"HTTP Error calling Gemini API: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        return ""

def main():
    config_path = "llm_build.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    global_context_path = config.get('global_context')
    global_context = read_file(global_context_path) if global_context_path else ""
    
    llm_config = config.get('llm_config', {})
    provider = llm_config.get('provider', 'mock')
    model = llm_config.get('model', 'gemini-1.5-flash')

    for target in config.get('targets', []):
        spec_path = target['spec']
        output_path = target['output_path']
        language = target.get('language', 'python')

        print(f"Compiling {spec_path} to {output_path} ({language}) using {provider}...")

        spec_content = read_file(spec_path)
        prompt = construct_prompt(global_context, spec_content, language)

        generated_code = ""
        if provider == 'mock':
            generated_code = mock_llm_generate(prompt)
        elif provider == 'google':
            api_key = os.environ.get("GEMINI_API_KEY")
            try:
                generated_code = google_llm_generate(prompt, model, api_key)
            except Exception as e:
                print(f"Error generating code: {e}")
                continue
        else:
            print(f"Unknown provider: {provider}")
            continue

        if generated_code:
            write_file(output_path, generated_code)
            print(f"Generated {output_path}")
        else:
            print(f"Failed to generate code for {spec_path}")

if __name__ == "__main__":
    main()
