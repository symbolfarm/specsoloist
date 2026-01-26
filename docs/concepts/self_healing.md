# Self-Healing

The self-healing loop is the "Magic" of Specular.

When a test fails, `specular fix` executes the following loop:

1.  **Analyze**: Feed the Spec, the Code, the Test, and the Failure Log to a Senior Engineer LLM agent.
2.  **Diagnose**: The agent determines if the error is in the Code (logic bug) or the Test (hallucinated expectation).
3.  **Patch**: The agent provides a minimal patch to resolve the discrepancy.
4.  **Verify**: The human can then run `specular test` to confirm the fix.
