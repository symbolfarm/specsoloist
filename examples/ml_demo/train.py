"""
Manual training loop (The "Experiment").
Imports Specular-generated components.
"""
import sys
import os

# Add build directory to path so we can import generated modules
sys.path.append(os.path.join(os.path.dirname(__file__), "build"))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader

# Import generated components
# Note: These will only exist after `specular compile` is run!
try:
    from model import SimpleMLP
    from data import SyntheticDataset
except ImportError:
    print("Error: Generated modules not found.")
    print("Please run: specular build")
    sys.exit(1)

def train():
    # 1. Setup
    torch.manual_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    # 2. Data
    dataset = SyntheticDataset(size=1000, input_dim=10)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    print(f"Dataset size: {len(dataset)}")

    # 3. Model
    model = SimpleMLP(input_dim=10, hidden_dim=64, output_dim=1).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()

    print(f"Model architecture:\n{model}")

    # 4. Loop
    model.train()
    for epoch in range(5):
        total_loss = 0
        for batch_idx, (data, target) in enumerate(dataloader):
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")

    print("Training complete.")

if __name__ == "__main__":
    train()
