# Specular

**Specular** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs to compile them into executable code.

## Why Specular?

Code is often messy, poorly documented, and prone to drift from original requirements. Specular flips the script:

1.  **Write the Spec**: Define your component in structured Markdown.
2.  **Compile to Code**: Specular uses LLMs (Gemini/Claude) to implement the spec.
3.  **Self-Healing**: If tests fail, Specular analyzes the failure and patches the code or tests automatically.

## Core Pillars

-   **Contracts over Code**: Define *what* you want, let the AI handle the *how*.
-   **Traceability**: Every line of code is directly linked to a Functional Requirement.
-   **Multi-Language**: Native support for Python and TypeScript.
