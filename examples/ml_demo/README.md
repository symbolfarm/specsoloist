# Machine Learning Demo

This example demonstrates the **Hybrid Workflow** for ML research using Specular.

1.  **Infrastructure (Specs)**: The Model architecture and Data pipeline are defined in rigorous specs (`src/*.spec.md`). This ensures reproducibility and shape correctness.
2.  **Experiment (Manual)**: The training loop (`train.py`) is written manually, allowing for rapid experimentation with hyperparameters and logging.

## Prerequisites

This example requires `torch`. It is isolated from the main package.

## Running the Demo

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Compile Infrastructure**:
    Use Specular to generate the PyTorch code for the model and dataset.
    ```bash
    # From project root
    specular build --root examples/ml_demo
    ```

3.  **Run Experiment**:
    Run the manual training script.
    ```bash
    python examples/ml_demo/train.py
    ```

## Why this approach?

*   **No Drift**: Your model definition is locked in a spec. You can't accidentally delete a layer without updating the requirements.
*   **Flexibility**: You can change learning rates, batch sizes, and logging in `train.py` without recompiling.
