---
name: data
type: bundle
status: stable
---

# 1. Overview
A synthetic dataset generator for machine learning regression tasks.
Generates data based on the linear relationship `y = 2x + noise`.

# 2. Interface Specification

```yaml:functions
get_dataset:
  inputs:
    size:
      type: integer
      default: 100
      description: "Number of samples to generate"
    input_dim:
      type: integer
      default: 10
      description: "Dimension of input features"
  outputs:
    dataset:
      type: object
      description: "An object implementing a standard dataset interface (length and indexed access)"
  behavior: "Creates and returns a dataset of synthetic inputs and targets."
```

## 2.1 Dataset Interface
The returned dataset object must provide:
*   **length**: Returns the total number of samples.
*   **item(index)**: Returns the input feature vector and target value at the given index.

# 3. Functional Requirements (Behavior)
*   **FR-01**: Data shall be generated using `torch.randn` for inputs.
*   **FR-02**: Targets shall be a linear combination of inputs plus random noise.
*   **FR-03**: The dataset shall be fully deterministic if a global seed is set externally.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Performance**: Generation should be vectorised (done at init or on fly).
*   **NFR-Framework**: Must implement standard PyTorch Dataset interface.

# 5. Design Contract
*   **Post-condition**: `__getitem__` returns tensors of type `float32`.

# 6. Test Scenarios
| Scenario | Input | Expected Output | Notes |
|----------|-------|-----------------|-------|
| Length check | `Dataset(size=50)` | `len() == 50` | Correct size |
| Item shape | `getitem(0)` | `(Tensor(10), Tensor(1))` | Correct feature/target shapes |
