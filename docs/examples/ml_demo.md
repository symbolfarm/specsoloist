# ML Research (PyTorch)

This example demonstrates the **Hybrid Workflow** for Machine Learning research.

In research, you need **Reproducibility** for your infrastructure (data loaders, model definitions) but **Flexibility** for your experiments (training loops, logging).

[View the Code in the repository](https://github.com/symbolfarm/specular/blob/main/examples/ml_demo)

### The Architecture

1.  **Specs (Infrastructure)**:
    *   `model.spec.md`: Defines the Neural Network architecture (layers, dimensions).
    *   `data.spec.md`: Defines the Data Pipeline (shapes, preprocessing).
2.  **Manual Code (Experiment)**:
    *   `train.py`: A hand-written script that imports the generated components and runs the training loop.

### Why this approach?

*   **Prevent Drift**: Your model architecture is locked in a spec. You can't accidentally change a layer size without updating the requirements.
*   **Rapid Iteration**: You can tweak hyperparameters, logging, and optimizers in `train.py` without needing to recompile the whole system.
