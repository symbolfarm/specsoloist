---
name: data
type: class
language_target: python
status: stable
dependencies: []
---

# 1. Overview
A synthetic dataset generator for regression testing.
Generates data `y = 2x + noise`.

# 2. Interface Specification

## 2.1 Class `SyntheticDataset`
Inherits from `torch.utils.data.Dataset`.

### `__init__(size: int = 100, input_dim: int = 10)`
*   `size`: Number of samples to generate.
*   `input_dim`: Dimension of input features.

### `__len__() -> int`
*   Returns the total size of the dataset.

### `__getitem__(idx: int) -> Tuple[torch.Tensor, torch.Tensor]`
*   Returns the `(input, target)` pair at the given index.

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
