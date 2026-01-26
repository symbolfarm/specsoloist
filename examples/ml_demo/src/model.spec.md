---
name: model
type: class
language_target: python
status: stable
dependencies: []
---

# 1. Overview
A simple Multi-Layer Perceptron (MLP) for regression tasks.
It maps a 10-dimensional input vector to a scalar output.

# 2. Interface Specification

## 2.1 Class `SimpleMLP`
Inherits from `torch.nn.Module`.

### `__init__(input_dim: int = 10, hidden_dim: int = 32, output_dim: int = 1)`
*   `input_dim`: Size of input features.
*   `hidden_dim`: Size of hidden layer.
*   `output_dim`: Size of output.

### `forward(x: torch.Tensor) -> torch.Tensor`
*   `x`: Input tensor of shape `(batch_size, input_dim)`.
*   **Returns**: Output tensor of shape `(batch_size, output_dim)`.

# 3. Functional Requirements (Behavior)
*   **FR-01**: The network shall have 3 linear layers.
*   **FR-02**: The hidden layers shall use ReLU activation functions.
*   **FR-03**: The final layer shall have no activation function (linear regression).

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Framework**: Must use PyTorch (`torch.nn`).
*   **NFR-TypeHinting**: All methods must have type hints.

# 5. Design Contract
*   **Pre-condition**: Input tensor `x` must match `input_dim`.
*   **Post-condition**: Output tensor must match `output_dim`.

# 6. Test Scenarios
| Scenario | Input | Expected Output | Notes |
|----------|-------|-----------------|-------|
| Forward Pass | Tensor `(1, 10)` | Tensor `(1, 1)` | Shape check |
| Batch Pass | Tensor `(16, 10)` | Tensor `(16, 1)` | Batch dimension preserved |
