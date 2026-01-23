# Specular Roadmap

## Phase 1: Core Framework & Self-Healing (Completed)
- [x] **Spec-as-Source**: Define components using rigorous SRS-style Markdown.
- [x] **LLM Compilation**: Compile specs to Python code using Google Gemini.
- [x] **Test Generation**: Automatically generate `pytest` suites from spec scenarios.
- [x] **Integrated Runner**: Run tests in isolated environments.
- [x] **Agentic Self-Healing**: `attempt_fix` loop that analyzes failures and patches code/tests.
- [x] **MCP Server**: Expose all tools via the Model Context Protocol.

## Phase 2: Architecture & Scalability (Next)
- [ ] **Dependency Graph**: Support importing types/functions across specs (e.g., `import { User } from 'types.spec.md'`).
- [ ] **Project-Level Specs**: `project.spec.md` to define global architecture and module boundaries.
- [ ] **Type Sharing**: A mechanism to share data structures between specs to ensure contract compatibility.
- [ ] **Incremental Builds**: Only recompile specs that have changed.

## Phase 3: Release Readiness (v1.0)
- [ ] **CLI Polish**: Rich terminal output (spinners, colored diffs) for the `specular` command.
- [ ] **Multi-Language Support**: Verify and template support for TypeScript and Go.
- [ ] **PyPI Publication**: Release `specular-ai` to PyPI.
- [ ] **Documentation Site**: Examples and API reference.

## Phase 4: Developer Experience
- [ ] **VS Code Extension**: Live preview of generated code/tests while editing specs.
- [ ] **Visual Spec Editor**: A GUI for defining Functional Requirements and Contracts.
- [ ] **Sandboxed Execution**: Run generated code in Docker containers for safety.
